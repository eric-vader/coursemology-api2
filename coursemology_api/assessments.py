from .utility import *
import io
import zipfile
import json
import time
import requests
import os
from collections import defaultdict


class Assessments(Rooted):

    URL = 'assessments'
    URL_ADMIN = 'admin/assessments'

    def __init__(self, root):
        super().__init__(root)
        self.Submissions = Submissions(self)

    @property
    @lru_cache(maxsize=1)
    def info(self):
        """
        As of now, self.URL will redirect to Missions and therefore unable to get the category and
        tab ID for Trainings without accessing URL_ADMIN.

        First workaround is to assume that both category ID and tab ID are increased by 1.
        Second workaround is to grant Manager/Owner access to whoever needs to scrape the Trainings section.
        """

        pages = []
        if self.include_all_assessments:
            try:
                response = self.HTTP.get(self.URL_ADMIN + self.URL_FORMAT_JSON)
                assert response.status_code == 200
                for category in response.json()['categories']:
                    cat_id = category['id']
                    cat_name = category['title']
                    for tab in category['tabs']:
                        tab_id = tab['id']
                        tab_name = tab['title']
                        pages.append((cat_id, cat_name, tab_id, tab_name))
            except AssertionError:
                cat_id = None
                for _ in range(2):
                    response = self.HTTP.get(
                        self.URL + self.URL_FORMAT_JSON + (f'&category={cat_id+1}' if cat_id else ''))
                    category = response.json()['display']['category']
                    cat_id = category['id']
                    cat_name = category['title']
                    for tab in category['tabs']:
                        tab_id = tab['id']
                        tab_name = tab['title']
                        pages.append((cat_id, cat_name, tab_id, tab_name))
        else:
            pages = [[None]*4]

        headers = ['Assessment ID', 'Assessment Name',
                   'Has Personal Times', 'Affects Personal Times', 'Is Draft', 'Is Password-Locked',
                   'Exp', 'Bonus Exp', 'Requirement For',
                   'Start At', 'Bonus End At', 'End At',
                   'Category ID', 'Category Name', 'Tab ID', 'Tab Name']

        data = []
        for category_id, category_name, tab_id, tab_name in pages:
            category = 'category' if category_id is None else f'category={category_id}'
            tab = 'tab' if tab_id is None else f'tab={tab_id}'
            response = self.HTTP.get(
                self.URL + self.URL_FORMAT_JSON + f'&{category}&{tab}')
            response_json = response.json()

            category_id = response_json['display']['category']['id']
            category_name = response_json['display']['category']['title']
            tab_id = response_json['display']['tabId']
            for assessment in response_json['assessments']:
                assessment_id = assessment['id']
                assessment_name = assessment['title']
                has_pt = assessment['hasPersonalTimes']
                affect_pt = assessment['affectsPersonalTimes']
                is_draft = not assessment['published']
                is_locked = assessment['published']
                exp = assessment.get('baseExp', '-')
                bonus_exp = assessment.get('timeBonusExp', '-')
                req_for = ';'.join(
                    cond['title'] for cond in assessment.get('topConditionals', {}))
                start_at = assessment.get(
                    'startAt', {}).get('referenceTime', '')
                bonus_cut_off = assessment.get(
                    'bonusEndAt', {}).get('referenceTime', '')
                end_at = assessment.get('endAt', {}).get('referenceTime', '')
                data.append([
                    assessment_id, assessment_name, has_pt, affect_pt, is_draft, is_locked,
                    exp, bonus_exp, req_for, start_at, bonus_cut_off, end_at,
                    category_id, category_name, tab_id, tab_name,
                ])
        return Table(headers=headers, data=data)

    @guess_id
    @lru_cache(maxsize=None)
    def __call__(self, id):
        return Assessment(self, id)


class Assessment(Rooted):

    def __init__(self, root, id):
        super().__init__(root, id)
        self.Submissions = Submissions(self)

    @property
    @lru_cache(maxsize=1)
    def info(self):
        response = self.HTTP.get(self.URL + self.URL_FORMAT_JSON)
        assert response.ok, f'Response not OK, status code is {response.status_code}'
        json_object = json.loads(response.content)

        headers = ['Question ID', 'Question Name', 'Question Type',
                   'Question URL', 'Question Duplication ID']
        data = []

        meta = {}
        meta['id'] = self.id
        meta['name'] = json_object['title']
        meta['type'] = json_object['autograded']
        meta['base_exp'] = int(json_object.get('baseExp', 0))
        meta['bonus_exp'] = int(json_object.get('timeBonusExp', 0))
        meta['start_at'] = json_object['startAt']['effectiveTime']
        try:
            meta['bonus_cut_off'] = json_object['bonusEndAt']['effectiveTime']
        except:
            meta['bonus_cut_off'] = None
        try:
            meta['end_at'] = json_object['endAt']['effectiveTime']
        except:
            meta['end_at'] = None
        meta['graded_test_case_types'] = json_object['gradedTestCases']
        meta['files'] = [(file['name'], self.URL_BASE + file['url'])
                         for file in json_object.get('files', [])]

        question_ids = [int(question['id'])
                        for question in json_object['questions']]
        question_duplication_ids = [int(question['duplicationUrls'][0]['destinations'][0]['duplicationUrl'].split(
            '/')[-3]) for question in json_object['questions']]
        question_names = [question['title']
                          for question in json_object['questions']]
        question_types = [question['type']
                          for question in json_object['questions']]
        question_urls = [self.URL_BASE + question['editUrl']
                         for question in json_object['questions']]
        assert len(question_ids) == len(question_names) == len(
            question_types) == len(question_urls), f'Unlucky scraping!'

        data = list(map(list, zip(question_ids, question_names,
                    question_types, question_urls, question_duplication_ids)))
        return Table(headers=headers, data=data, meta=meta)

    def download(self, directory=None):
        '''Downloads file attachements and test packages'''
        directory = f"data/{self.course_id}/tests/{str2path(self.info.meta['name'])}" if directory is None else directory
        os.makedirs(directory, exist_ok=True)
        self.download_files(directory)
        self.download_tests(directory)
        return directory

    def download_files(self, directory=None):
        '''Downloads assessment file attachements'''
        directory = f"data/{self.course_id}/tests/{str2path(self.info.meta['name'])}" if directory is None else directory
        os.makedirs(directory, exist_ok=True)
        for filename, url in self.info.meta['files']:
            response = self.HTTP.get(url + self.URL_FORMAT_JSON)
            assert response.ok, response.status_code
            download_url = response.json()['url']
            file_response = self.HTTP.get(download_url)
            with open(f'{directory}/{filename}', 'wb') as f:
                f.write(file_response.content)
        return directory

    def download_tests(self, directory=None):
        '''Downloads test packages'''
        directory = f"data/{self.course_id}/tests/{str2path(self.info.meta['name'])}" if directory is None else directory
        os.makedirs(directory, exist_ok=True)
        for i, (question_id, question_name, question_type, question_url) in enumerate(self.info.data):
            if question_name == '':
                question_name = f'Question {i+1}'
            if question_type == 'Programming':
                response = self.HTTP.get(question_url + self.URL_FORMAT_JSON)
                json_object = json.loads(response.content)
                if json_object['question']['package'] is None:
                    continue
                package = self.URL_BASE + \
                    json_object['question']['package']['path']
                response = self.HTTP.get(package)
                zip_document = zipfile.ZipFile(io.BytesIO(response.content))
                zip_document.extractall(directory + f'/{question_name}')
        return directory

    def move(self, target_tab_id):
        '''Moves assessment from current tab to target tab'''
        json_payload = {
            'assessment': {
                'tab_id': target_tab_id,
            }
        }
        headers = {"X-Csrf-Token": self.auth_token}
        return self.HTTP.patch(self.URL + self.URL_FORMAT_JSON, data=None, json=json_payload, headers=headers, allow_redirects=False)

    def publish(self):
        json_payload = {
            'assessment': {
                'published': True
            }
        }
        headers = {"X-Csrf-Token": self.auth_token}
        return self.HTTP.patch(self.URL + self.URL_FORMAT_JSON, data=None, json=json_payload, headers=headers, allow_redirects=False)

    def unpublish(self):
        json_payload = {
            'assessment': {
                'published': False
            }
        }
        headers = {"X-Csrf-Token": self.auth_token}
        return self.HTTP.patch(self.URL + self.URL_FORMAT_JSON, data=None, json=json_payload, headers=headers, allow_redirects=False)

    def skippable(self, is_skippable):
        json_payload = {
            'assessment': {
                'skippable': is_skippable
            }
        }
        headers = {"X-Csrf-Token": self.auth_token}
        return self.HTTP.patch(self.URL + self.URL_FORMAT_JSON, data=None, json=json_payload, headers=headers, allow_redirects=False)

    def duplicate(self, question, assessment_id_or_name):
        question_id = get_question_id(self, question, idx=4)
        assessment_id = self.Assessments(assessment_id_or_name).id
        headers = {"X-Csrf-Token": self.auth_token}
        return self.HTTP.post(f'{self.URL}/questions/{question_id}/duplicate/{assessment_id}' + self.URL_FORMAT_JSON, data=None, headers=headers, allow_redirects=False)

    def delete(self):
        '''Deletes assessment [DANGEROUS]'''
        formdata = {
            '_method': 'delete',
            'authenticity_token': self.auth_token,
        }
        return self.HTTP.post(self.URL, data=formdata, allow_redirects=False)


class Submissions(Rooted):

    URL = 'submissions'
    URL_STATS = 'submissions/download_statistics'

    STATUS_PUBLISHED = 'published'
    STATUS_GRADED = 'graded'
    STATUS_SUBMITTED = 'submitted'
    STATUS_ATTEMPTING = 'attempting'
    STATUS_UNSTARTED = 'unstarted'

    @property
    def info(self):
        if isinstance(self.root, Assessment):
            return self.info_assessment
        return self.info_pending

    @property
    @lru_cache(maxsize=1)
    def info_assessment(self):
        response = self.HTTP.get(self.URL + self.URL_FORMAT_JSON)
        json_object = json.loads(response.content)

        headers = ['Submission ID', 'User Name', 'User ID', 'Student',
                   'Submission Status', 'Grade', 'Max Grade', 'Exp',
                   'Submitted At', 'Graded At', 'Phantom']

        meta = {}
        meta['assessment_id'] = self.id
        meta['assessment_name'] = json_object['assessment']['title']
        meta['max_grade'] = json_object['assessment']['maximumGrade']

        if self.include_submissions_breakdown:
            # data = self.root.info.data
            # headers.extend(['Attempted At'] +
            #                 [f'Q{i+1}' for i in range(num_questions)])
            pass

        data = []
        for submission in json_object['submissions']:
            is_phantom = submission['courseUser']['phantom']
            if not self.include_phantoms and is_phantom:
                continue  # skip phantoms if not tracking
            submission = defaultdict(lambda: None, submission)
            user_id = submission['courseUser']['id']
            user_name = submission['courseUser']['name']
            is_student = submission['courseUser']['isStudent']
            status = submission['workflowState']
            grade = submission['grade']
            exp = submission['pointsAwarded']
            submitted_at = submission['dateSubmitted']
            graded_at = submission['dateGraded']
            submission_id = submission['id']

            datum = [submission_id, user_name, user_id, is_student, status,
                     grade, meta['max_grade'], exp, submitted_at, graded_at, is_phantom]

            data.append(datum)
        return Table(headers=headers, data=data, meta=meta)

    @property
    @lru_cache(maxsize=1)
    def info_pending(self):
        meta = None
        records = []
        i = 1
        while True:
            response = self.HTTP.get(self.URL + f'/pending?filter[page_num]={i}&format=json')
            assert response.ok
            response_json = response.json()
            if meta is None:
                meta = response_json['metaData']
            if response_json['submissions'] == []:
                break
            for submission in response_json['submissions']:
                submission = defaultdict(lambda: None, submission)
                record = {
                    'Submission ID': submission['id'],
                    'User Name': submission['courseUserName'],
                    'User ID' : submission['courseUserId'],
                    'Assessment ID' : submission['assessmentId'],
                    'Assessment Title': submission['assessmentTitle'],
                    'Submission Status':  submission['status'],
                    'Grade': submission['maxGrade'],
                    'Max Grade': submission['maxGrade'],
                    'Exp': submission['pointsAwarded'],
                    'Submitted At': submission['submittedAt']
                }
                for idx, teaching_staff in enumerate(submission['teachingStaff']):
                    record[f'Teaching Staff ID {idx+1}'] = teaching_staff['teachingStaffId']
                    record[f'Teaching Staff Name {idx+1}'] = teaching_staff['teachingStaffName']

                records.append(record)
            i += 1
        df = pd.DataFrame.from_records(records)
        return Table(headers=df.columns.to_list(), data=df.values.tolist(), meta=meta)

    @property
    @lru_cache(maxsize=1)
    def stats(self):
        import csv
        import time
        response = self.HTTP.get(self.URL_STATS + self.URL_FORMAT_JSON)
        response_json = response.json()
        job_url = None
        while True:
            if 'redirectUrl' in response_json:
                redirect_url = response_json['redirectUrl']
                with self.HTTP.get(self.URL_BASE + redirect_url, stream=True) as r:
                    lines = (line.decode('utf-8') for line in r.iter_lines())
                    reader = csv.reader(lines)
                    headers = next(reader)
                    data = [line for line in reader]
                return Table(headers=headers, data=data)
            elif 'jobUrl' in response_json:
                time.sleep(1)
                if not job_url:
                    job_url = response_json['jobUrl']
                response = self.HTTP.get(
                    f"{self.URL_BASE}{job_url}" + self.URL_FORMAT_JSON)
                response_json = response.json()
            elif 'error' in response_json:
                return Table(headers=[], data=[])
            else:
                raise Exception('Any other cases to consider??')

    @property
    @lru_cache(maxsize=1)
    def outputs(self):
        raise NotImplementedError # TODO

    def download(self, directory=None, max_workers=None):
        '''Downloads all graded submissions'''
        import concurrent.futures
        directory = f"data/{self.course_id}/submissions/{str2path(self.info.meta['assessment_name'])}" if directory is None else directory
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = []
            for row in self.info.data:
                submission_id, submission_name, submitted_at = row[0], row[1], row[8]
                filename = f"{self.course_id}.{self.id}.{submission_id}.{str2path(submission_name)}.csv"
                if submitted_at is not None:
                    executor.submit(self(submission_id).download,
                                    filename=filename, directory=directory)
        return directory

    def download_all(self, directory=None, check_interval=3):
        '''Downloads all submissions as zip'''
        import concurrent.futures
        directory = f"data/{self.course_id}/submissions/{str2path(self.info.meta['assessment_name'])}" if directory is None else directory
        os.makedirs(directory, exist_ok=True)
        download_url = self.URL + '/download_all' + self.URL_FORMAT_JSON + '&course_users=students&download_format=zip'
        response = self.HTTP.get(download_url)
        while True:
            response_json = response.json()
            if response_json['status'] == 'completed':
                break
            time.sleep(check_interval)
            response = self.HTTP.get(self.URL_BASE + response_json['jobUrl'] + self.URL_FORMAT_JSON)
        zip_file_url = response_json['redirectUrl']
        response = requests.get(zip_file_url)
        z = zipfile.ZipFile(io.BytesIO(response.content))
        z.extractall(directory)
        return directory

    @lru_cache(maxsize=1)
    def pending(self, my_students=False):
        URL_MY_STUDENTS = '&my_students=' + ('true' if my_students else 'false')
        url = f'{self.URL}/pending{self.URL_FORMAT_JSON}{URL_MY_STUDENTS}'
        return get_default_info_table(self, url=url, records_key='submissions', meta_keys=['metaData', 'permissions'])

    @guess_id
    @lru_cache(maxsize=None)
    def __call__(self, id):
        return Submission(self, id)


class Submission(Rooted):

    TYPE_MCQ = 'MultipleChoice'
    TYPE_MRQ = 'MultipleResponse'
    TYPE_TEXT = 'TextResponse'
    TYPE_FILE = 'FileUpload'
    TYPE_CODE = 'Programming'
    TYPE_AUDIO = 'AudioResponse'  # unhandled, unverified identifier
    TYPE_SCRIBE = 'Scribing'     # unhandled, unverified identifier

    def set_info_json(self):
        response = self.HTTP.get(self.URL + '/edit' + self.URL_FORMAT_JSON)
        self._info_json = json.loads(response.content)

    @property
    @lru_cache(maxsize=1)
    def info(self):
        try:
            json_object = self._info_json
        except Exception as e:
            response = self.HTTP.get(self.URL + '/edit' + self.URL_FORMAT_JSON)
            json_object = json.loads(response.content)
        submission = defaultdict(str, json_object['submission'])
        assessment = json_object['assessment']
        questions = {q['id']: q for q in json_object['questions']}
        answers = {a['id']: a for a in json_object['answers']}

        meta = {}
        meta['id'] = self.id
        meta['assessment_name'] = assessment['title']
        meta['category_id'] = assessment['categoryId']
        meta['tab_id'] = assessment['tabId']

        meta['status'] = submission['workflowState']
        meta['student_name'] = submission['submitter']
        meta['grader_name'] = submission['grader']

        meta['attempted_at'] = submission['attemptedAt']
        meta['submitted_at'] = submission['submittedAt']
        meta['graded_at'] = submission['gradedAt']
        meta['due_at'] = submission['dueAt']
        meta['bonus_end_at'] = submission['bonusEndAt']

        meta['grade'] = submission['grade']
        meta['max_grade'] = submission['maximumGrade']
        meta['base_exp'] = submission['basePoints']
        meta['bonus_exp'] = submission['bonusPoints']
        meta['awarded_exp'] = submission['pointsAwarded']
        meta['is_late'] = submission['late']

        meta['show_output'] = submission['showPublicTestCasesOutput']
        meta['show_error'] = submission['showStdoutAndStderr']

        meta['files'] = [(file['name'], self.URL_BASE + file['url'])
                         for file in assessment['files']]

        meta['posts'] = json_object['posts']

        headers = ['Submission Question ID', 'Question Name', 'Question ID', 'Question Type',
                   'Answer ID', 'Answer', 'Answer Meta Info', 'Grade', 'Max Grade',
                   'Tests Passed Count', 'Tests Total Count', 'Submission Created At',
                   'Answer Option ID', 'Answer Correct', 'Test Cases']

        data = []
        extras = []
        for question_id in assessment['questionIds']:
            submission_question_id = questions[question_id]['submissionQuestionId']
            question_name = questions[question_id]['questionTitle']
            answer_id = questions[question_id]['answerId']
            if answer_id is not None:
                created_at = answers[answer_id]['createdAt']
                grade = answers[answer_id]['grading']['grade']
            else:
                created_at = None
                grade = None
            max_grade = questions[question_id]['maximumGrade']
            question_type = questions[question_id]['type']
            answer_meta_info = ''
            tests_pass = tests_total = ''
            answer_option_id = ''
            answer_correct = ''
            test_public_total = test_private_total = test_eval_total = 0
            test_public_pass = test_private_pass = test_eval_pass = 0
            test_cases = ''
            extra = {}
            if answer_id is None:
                pass # do nothing
            elif question_type == self.TYPE_MCQ:
                try:
                    options = {
                        option['id']: option for option in questions[question_id]['options']}
                    answer = ';'.join(
                        options[opt_id]['option'] for opt_id in answers[answer_id]['fields']['option_ids'])
                    answer_option_id = ';'.join(
                        str(opt_id) for opt_id in answers[answer_id]['fields']['option_ids'])
                    answer_correct = answers[answer_id]['explanation']['correct'] if 'explanation' in answers[answer_id] else ''
                except:
                    answer = ''
            elif question_type == self.TYPE_MRQ:
                try:
                    options = {
                        option['id']: option for option in questions[question_id]['options']}
                    answer = ';'.join(
                        options[opt_id]['option'] for opt_id in answers[answer_id]['fields']['option_ids'])
                except:
                    answer = ''
            elif question_type == self.TYPE_TEXT:
                try:
                    answer = answers[answer_id]['fields']['answer_text']
                except:
                    answer = ''
            elif question_type == self.TYPE_FILE:
                answer = self.URL_BASE + '/attachments/' + attachments[0]['id'] \
                    if (attachments := answers[answer_id]['attachments']) else ''
            elif question_type == self.TYPE_CODE:
                ans = answers[answer_id]
                try:
                    answer = ans['fields']['files_attributes'][0]['content']
                    answer_meta_info = ans['fields']['files_attributes'][0]['id']
                except:
                    answer = ''
                    answer_meta_info = ''
                if 'testCases' in ans:
                    extra['testCases'] = ans['testCases']
                    test_public_pass = sum(
                        'passed' in test and test['passed'] for test in ans['testCases']['public_test']) if 'public_test' in ans['testCases'] else 0
                    test_private_pass = sum(
                        'passed' in test and test['passed'] for test in ans['testCases']['private_test']) if 'private_test' in ans['testCases'] else 0
                    test_eval_pass = sum('passed' in test and test['passed'] for test in ans['testCases']
                                         ['evaluation_test']) if 'evaluation_test' in ans['testCases'] else 0
                    test_public_total = len(
                        ans['testCases']['public_test']) if 'public_test' in ans['testCases'] else 0
                    test_private_total = len(
                        ans['testCases']['private_test']) if 'private_test' in ans['testCases'] else 0
                    test_eval_total = len(
                        ans['testCases']['evaluation_test']) if 'evaluation_test' in ans['testCases'] else 0
                    tests_pass = f'{test_public_pass};{test_private_pass};{test_eval_pass}'
                    tests_total = f'{test_public_total};{test_private_total};{test_eval_total}'
                    test_public_cases = ','.join('1' if (
                        'passed' in test and test['passed']) else '0' for test in ans['testCases']['public_test']) if 'public_test' in ans['testCases'] else ''
                    test_private_cases = ','.join('1' if (
                        'passed' in test and test['passed']) else '0' for test in ans['testCases']['private_test']) if 'private_test' in ans['testCases'] else ''
                    test_eval_cases = ','.join('1' if (
                        'passed' in test and test['passed']) else '0' for test in ans['testCases']['evaluation_test']) if 'evaluation_test' in ans['testCases'] else ''
                    test_cases = f'{test_public_cases};{test_private_cases};{test_eval_cases}'
            else:
                answer = f'UNHANDLED QUESTION TYPE: {question_type}'
            data.append([
                submission_question_id, question_name, question_id, question_type,
                answer_id, answer, answer_meta_info, grade, max_grade,
                tests_pass, tests_total, created_at, answer_option_id, answer_correct, test_cases
            ])

            # response = self.HTTP.get(f'{self.root.root.URL}/submission_questions/{submission_question_id}/past_answers' + self.URL_FORMAT_JSON)
            # extra['past_answers'] = json.loads(response.content)

            extras.append(extra)
        meta['extras'] = extras
        return Table(headers=headers, data=data, meta=meta)

    @property
    @lru_cache(maxsize=1)
    def outputs(self):
        raise NotImplementedError # TODO

    def download(self, filename=None, directory=None):
        directory = f"data/{self.course_id}/submissions/{str2path(self.info.meta['assessment_name'])}" if directory is None else directory
        os.makedirs(directory, exist_ok=True)
        filename = f"{self.course_id}.{self.root.id}.{self.id}.{str2path(self.info.meta['student_name'])}.csv" if filename is None else filename
        filepath = f"{directory}/{filename}"
        if not os.path.exists(filepath):
            self.info.to_csv(filepath)
        return directory

    def submit(self):
        ''' Should not use this, since we should allow students to submit missions on their own '''
        formdata = {'[submission][finalise]': True}
        headers = {"X-Csrf-Token": self.auth_token}
        return self.HTTP.patch(self.URL, data=formdata, headers=headers, allow_redirects=False)

    def compute_exp(self, total_grades, multiplier):
        meta = self.info.meta
        exp = meta['base_exp']
        exp = exp if meta['is_late'] else exp + meta['bonus_exp']
        return round(multiplier * exp * total_grades / meta['max_grade'])

    def grade(self, *grades, multiplier=1.0, publish=False):
        assert 0 <= multiplier <= 1.0, f'multiplier must be in the range [0.0, 1.0]. Was given {multiplier}'
        answer_ids, existing_grades, max_grades = zip(
            *[(row[4], row[7], row[8]) for row in self.info.data])

        if grades != ():
            assert len(grades) == len(max_grades) and \
                all(int(grade) <= int(max_grade) for grade, max_grade in zip(grades, max_grades)), \
                f'({len(max_grades)}) maximum grades {max_grades} expected. Was given ({len(grades)}) grades {grades} instead.'
        else:
            grades = existing_grades

        exp_type = 'points_awarded' if self.info.meta[
            'status'] == self.STATUS_PUBLISHED else 'draft_points_awarded'
        formdata = [(f'[submission][{exp_type}]',
                     self.compute_exp(sum(grades), multiplier))]
        for grade, answer_id, max_grade in zip(grades, answer_ids, max_grades):
            formdata.append(('[submission][answers][][id]', answer_id))
            formdata.append(('[submission][answers][][grade]', grade))
        if publish and self.info.meta['status'] != self.STATUS_PUBLISHED:
            formdata.append(('[submission][publish]', True))
        headers = {"X-Csrf-Token": self.auth_token}
        return self.HTTP.patch(self.URL + self.URL_FORMAT_JSON, data=formdata, headers=headers, allow_redirects=False)

    def publish(self):
        ''' If there is no existing grades, submission gets published with 0 grades. '''
        formdata = {'[submission][publish]': True}
        headers = {"X-Csrf-Token": self.auth_token}
        return self.HTTP.patch(self.URL, data=formdata, headers=headers, allow_redirects=False)

    def mark(self):
        ''' If there is no existing grades, submission gets marked with 0 grades (marked but grades not publish). '''
        formdata = {'[submission][mark]': True}
        headers = {"X-Csrf-Token": self.auth_token}
        return self.HTTP.patch(self.URL, data=formdata, headers=headers, allow_redirects=False)

    def unsubmit(self):
        formdata = {'[submission][unsubmit]': True}
        headers = {"X-Csrf-Token": self.auth_token}
        return self.HTTP.patch(self.URL, data=formdata, headers=headers, allow_redirects=False)

    def set_exp(self, exp):
        formdata = {'[submission][points_awarded]': exp}
        headers = {"X-Csrf-Token": self.auth_token}
        return self.HTTP.patch(self.URL, data=formdata, headers=headers, allow_redirects=False)

    def comment(self, question, text=''):
        if text.strip() == '':
            raise ValueError("You need to specify some HTML text to comment.")
        question_id = get_question_id(self, question)
        target_url = self.root.root.URL + \
            f'/submission_questions/{question_id}/comments?format=json'
        headers = {"X-Csrf-Token": self.auth_token}
        payload = {"discussion_post": {"text": text}}
        return self.HTTP.post(target_url, data=None, json=payload, headers=headers, allow_redirects=False)

    def annotate(self, question, line, text=''):
        question_id_to_answer_data = {
            row[0]: (row[4], row[6]) for row in self.info.data}
        question_id = get_question_id(self, question)
        answer_id, file_id = question_id_to_answer_data[question_id]
        headers = {"X-Csrf-Token": self.auth_token}
        payload = {
            "annotation": {"line": line},
            "discussion_post": {"text": text}
        }
        target_url = self.URL + \
            f'/answers/{answer_id}/programming/files/{file_id}/annotations' + \
            self.URL_FORMAT_JSON
        return self.HTTP.post(target_url, data=None, json=payload, headers=headers, allow_redirects=False)

    def flush_cache(self):
        self.__class__.info.fget.cache_clear()
