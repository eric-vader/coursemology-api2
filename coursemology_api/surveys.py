from .utility import *
import contextlib
import csv
import codecs

class Surveys(Rooted):

    URL = 'surveys'

    @property
    @lru_cache(maxsize=1)
    def info(self):
        response = self.HTTP.get(self.URL + self.URL_FORMAT_JSON)
        surveys = response.json()['surveys']

        headers = ['Survey ID', 'Name', 'Base Points', 'Bonus Points', 'Opens At', 'Expires At', 'Bonus ends at', 'Reminder at', 'Published', 'Anonymous']

        data = []
        for survey in surveys:
            survey_id    = survey['id']
            name         = survey['title']
            base         = survey['base_exp']
            bonus        = survey['time_bonus_exp']
            is_published = survey['published']
            start_at     = survey['start_at']
            end_at       = survey['end_at']
            bonus_end_at = survey['bonus_end_at']
            reminder_at  = survey['closing_reminded_at']
            is_anonymous = survey['anonymous']

            allow_response_after_end  = survey['allow_response_after_end']
            allow_modify_after_submit = survey['allow_modify_after_submit']

            data.append([survey_id, name, base, bonus, start_at, end_at, bonus_end_at, reminder_at, is_published, is_anonymous])
        return Table(headers=headers, data=data)

    @guess_id
    @lru_cache(maxsize=None)
    def __call__(self, id):
        return Survey(self, id)

class Survey(Rooted):

    COMPLETED   = 'submitted'
    IN_PROGRESS = 'responding'
    UNCOMMENCED = 'not started'

    def __init__(self, root, id):
        super().__init__(root, id)
        self.URL_RESULTS = self.URL + '/results'
        self.URL_RESPONSES = self.URL + '/responses'

    @property
    @lru_cache(maxsize=1)
    def info(self):
        response = self.HTTP.get(self.URL_RESPONSES + self.URL_FORMAT_JSON)
        json_object = response.json()

        headers = ['Student ID', 'Student Name', 'Phantom', 'Submission Status',
                'Submitted At']

        meta = {}
        meta['survey_id'] = json_object['survey']['id']
        meta['survey_name'] = json_object['survey']['title']
        meta['base_exp'] = json_object['survey']['base_exp']
        meta['bonus_exp'] = json_object['survey']['time_bonus_exp']
        meta['published'] = json_object['survey']['published']
        meta['start_at'] = json_object['survey']['start_at']
        meta['end_at'] = json_object['survey']['end_at']
        meta['allow_response_after_end'] = json_object['survey']['allow_response_after_end']
        meta['allow_modify_after_submit'] = json_object['survey']['allow_modify_after_submit']
        meta['description'] = json_object['survey']['description']
        meta['canUpdate'] = json_object['survey']['canUpdate']
        meta['canDelete'] = json_object['survey']['canDelete']
        meta['canCreateSection'] = json_object['survey']['canCreateSection']
        meta['canRespond'] = json_object['survey']['canRespond']
        meta['hasStudentResponse'] = json_object['survey']['hasStudentResponse']
        meta['anonymous'] = json_object['survey']['anonymous']

        data = []
        for resp in json_object['responses']:
            course_user = resp['course_user']
            is_phantom = course_user['phantom']
            if not self.include_phantoms and is_phantom:
                continue
            student_id = course_user['id']
            student_name = course_user['name']
            status = self.COMPLETED if resp['present'] and resp['submitted_at'] else \
                        self.IN_PROGRESS if resp['present'] else \
                        self.UNCOMMENCED
            submitted_at = resp['submitted_at'] if status == self.COMPLETED else ''
            data.append([student_id, student_name, is_phantom, status, submitted_at])

        if meta['anonymous']:
            print("Survey is anonymous, fall-back to export the responses via download.")
            response = self.HTTP.get(self.URL + '/download' + self.URL_FORMAT_JSON)
            url_job = self.URL_BASE + response.json()['redirect_url']
            response = self.HTTP.get(url_job)
            line_iterator = (x.decode('utf-8') for x in response.iter_lines(decode_unicode=True))
            reader = csv.reader(line_iterator, delimiter=',', quotechar='"')
            extra_headers = next(reader)[4:]
            headers.extend(extra_headers)
            data_table = defaultdict(dict)
            for row in reader:
                user_id = int(row[1])
                data_table[user_id] = row[4:]
            for row in data:
                user_id = row[0]
                if user_id in data_table:
                    row.extend(data_table[user_id])
                else:
                    row.extend([''] * len(extra_headers))
            return Table(headers=headers, data=data, meta=meta)

        response = self.HTTP.get(self.URL_RESULTS + self.URL_FORMAT_JSON)
        json_object = response.json()
        sections = json_object['sections']

        header_ids = []
        data_table = defaultdict(dict)
        for section in sorted(sections, key=lambda s: s['weight']):
            for question in sorted(section['questions'], key=lambda q: q['weight']):
                headers.append(question['description'])
                header_ids.append(question['id'])
                oid2text = {opt['id']: opt['option'] for opt in question['options']}
                for answer in question['answers']:
                    user_id = answer['course_user_id']
                    if 'question_option_ids' in answer:
                        response = [oid2text[option_id] for option_id in answer['question_option_ids']]
                    elif 'text_response' in answer:
                        response = answer['text_response']
                    else:
                        raise Exception("Unhandled response type: " + str(answer))
                    data_table[user_id][question['id']] = response

        for row in data:
            user_id = row[0]
            if user_id in data_table:
                row.extend([data_table[user_id][qid] for qid in header_ids])
            else:
                row.extend([''] * len(header_ids))
        return Table(headers=headers, data=data, meta=meta)
