from .utility import *

from tqdm_loggable.auto import tqdm

class Users(Rooted):

    URL = 'users'
    URL_INVITATIONS = 'user_invitations'

    def __init__(self, root):
        super().__init__(root)
        self.Students = Students(self, skip_url=True)
        self.Staff = Staff(self, skip_url=True)

    @property
    @lru_cache(maxsize=1)
    def info(self):
        '''get both students and staff info'''
        headers = ['User ID', 'Name', 'Email',
                   'Timeline Algorithm', 'Role', 'Phantom']
        data = self.Staff.info.data + self.Students.info.data
        return Table(headers=headers, data=data)

    def exp_disburse(self, reason_for_disbursement, student_id_exp_pairs=[], return_report=False):
        if len(student_id_exp_pairs) == 0:
            return [] if return_report else None
        formdata = {
            'utf8': '✓',
            'authenticity_token': self.auth_token,
            'commit': 'Disburse Points',
            'experience_points_disbursement[reason]': reason_for_disbursement,
        }
        prefix = 'experience_points_disbursement[experience_points_records_attributes]'

        for i, id_exp in enumerate(student_id_exp_pairs):
            formdata[f'{prefix}[{i}][course_user_id]'] = id_exp[0]
            formdata[f'{prefix}[{i}][points_awarded]'] = id_exp[1]

        response = self.HTTP.post(self.URL + '/disburse_experience_points' + self.URL_FORMAT_JSON, data=formdata, allow_redirects=False)
        if return_report:
            return [{'User ID': student_id, 'EXP': exp, 'Method': 'Create', 'OK': response.ok} for student_id, exp in student_id_exp_pairs]
        return response

    def exp_disburse_override(self, reason_for_disbursement, student_id_exp_pairs=[], progress_bar=False):
        exp_records_info = self.ExpRecords.get_info(progress_bar=progress_bar)
        df = exp_records_info.df[exp_records_info.df['Reason'] == reason_for_disbursement]

        student_id_exp_pairs = student_id_exp_pairs
        student_id_exp_dict = {s:e for s,e in student_id_exp_pairs}
        student_ids = [s for s,i in student_id_exp_pairs]

        create = list(set(student_ids) - set(df['User ID'].to_list()))
        create_student_id_exp_pairs = [(s,e) for s,e in student_id_exp_pairs if s in create]

        update_candidate_df = df.loc[df['User ID'].isin(student_ids)]
        unchanged_df = pd.DataFrame.from_records(
            [{**item, **{'EXP': student_id_exp_dict[item['User ID']]}}
             for item in update_candidate_df.to_dict('records') if student_id_exp_dict[item['User ID']] == item['Experience Points Awarded']]
        )
        update_df = pd.DataFrame.from_records(
            [{**item, **{'EXP': student_id_exp_dict[item['User ID']]}}
             for item in update_candidate_df.to_dict('records') if student_id_exp_dict[item['User ID']] != item['Experience Points Awarded']]
        )
        update_student_id_record_exp_pairs = update_df[['User ID', 'Record ID', 'EXP']].values.tolist() if update_df.shape[0] > 0 else []

        create_result = self.exp_disburse(reason_for_disbursement, student_id_exp_pairs=create_student_id_exp_pairs, return_report=True)
        update_result = self.exp_override(reason_for_disbursement, student_id_record_exp_pairs=update_student_id_record_exp_pairs)
        unchanged_result = [{'User ID': record['User ID'], 'Record ID': record['Record ID'], 'EXP': record['EXP'], 'Method': 'Unchanged', 'OK': True}
                            for record in unchanged_df.to_dict('records')]

        return pd.DataFrame.from_records(create_result + update_result + unchanged_result)

    def exp_override(self, reason_for_disbursement, student_id_record_exp_pairs):
        result = []
        for student_id, record_id, exp in student_id_record_exp_pairs:
            record = self.Students(student_id).ExpRecords(record_id)
            response = record.update(reason=reason_for_disbursement, exp=exp)
            result.append({'User ID': student_id, 'Record ID': record_id, 'EXP': exp, 'Method': 'Update', 'OK': response.ok})
        return result

    def invite(self, data):
        '''data = [[Name, Email, Role, Is Phantom], ...]'''

        formdata = {
            'utf8': '✓',
            'authenticity_token': self.auth_token
        }
        prefix = 'course[invitations_attributes]'

        for i, (name, email, role, phantom) in enumerate(data):
            formdata[f'{prefix}[{i}][name]'] = name
            formdata[f'{prefix}[{i}][email]'] = email
            formdata[f'{prefix}[{i}][role]'] = role
            formdata[f'{prefix}[{i}][phantom]'] = phantom

        return self.HTTP.post(self.URL + '/invite' + self.URL_FORMAT_JSON, data=formdata, allow_redirects=False)

    @property
    @lru_cache(maxsize=1)
    def invitations(self):
        response = self.HTTP.get(self.URL_INVITATIONS + '?format=json')
        assert response.ok, f'Response not OK, status code is {response.status_code}'

        headers = ['ID', 'Name', 'Email', 'Role', 'Phantom', 'Timeline Algorithm', 'Invitation Code', 'Invitation Sent At', 'Confirmed']

        data = []
        for user in response.json()['invitations']:
            user_id = user['id']
            user_name = user['name']
            email = user['email']
            role = ' '.join(map(lambda x: x.capitalize(), user['role'].split('_')))
            is_phantom = user['phantom']
            timeline_algorithm = user['timelineAlgorithm']
            invitation_key = user['invitationKey']
            sent_at = user['sentAt']
            confirmed = user['confirmed']
            data.append([user_id, user_name, email, role, is_phantom, timeline_algorithm, invitation_key, sent_at, confirmed])
        return Table(headers=headers, data=data)

    @property
    def pending_invitations(self):
        headers = ['ID', 'Name', 'Email', 'Role', 'Phantom', 'Timeline Algorithm', 'Invitation Code', 'Invitation Sent At', 'Confirmed']
        data = [u for u in self.Users.invitations.data if not u[-1]]
        return Table(headers=headers, data=data)


    @guess_id
    @lru_cache(maxsize=None)
    def __call__(self, id):
        return User(self, id)


class User(Rooted):

    def __init__(self, root, id):
        super().__init__(root, id)
        self.ExpRecords = ExpRecords(self)
        self.PersonalTimes = PersonalTimes(self)

    @property
    @lru_cache(maxsize=1)
    def info(self):
        raise Exception('TODO: maybe put random deets here?')

    def update(self, name=None, timeline_algorithm=None, phantom=None):
        ''' Updates user settings.
        name: str
        timeline_algorithm: 'fixed'|'fomo'|'stragglers'|'otot'
        phantom: 0|1
        '''
        formdata = {}
        if name is not None:
            formdata['course_user[name]'] = name
        if timeline_algorithm is not None:
            formdata['course_user[timeline_algorithm]'] = timeline_algorithm
        if phantom is not None:
            formdata['course_user[phantom]'] = phantom
        headers = {"X-Csrf-Token": self.auth_token}
        return self.HTTP.patch(self.URL + self.URL_FORMAT_JSON, data=formdata, headers=headers, allow_redirects=False)

    def delete(self):
        self.root.flush_cache()
        formdata = {
            '_method': 'delete'
        }
        headers = {
            'X-CSRF-Token': self.auth_token,
        }
        return self.HTTP.post(self.URL, data=formdata, headers=headers)

class Students(Rooted):

    URL = 'students'
    URL_STATS = 'statistics/students'

    @property
    @lru_cache(maxsize=1)
    def info(self):
        response = self.HTTP.get(self.URL + self.URL_FORMAT_JSON)
        assert response.ok, f'Response not OK, status code is {response.status_code}'

        headers = ['User ID', 'Name', 'Email',
                   'Timeline Algorithm', 'Role', 'Phantom']

        data = []
        for user in response.json()['users']:
            user_id = user['id']
            user_name = user['name']
            email = user['email']
            timeline = user.get('timelineAlgorithm')
            is_phantom = user['phantom']
            if not self.include_phantoms and is_phantom:
                continue  # skip phantoms if not tracking
            data.append([user_id, user_name, email,
                        timeline, 'Student', is_phantom])
        return Table(headers=headers, data=data)

    @property
    @lru_cache(maxsize=1)
    def stats(self):
        response = self.HTTP.get(self.URL_STATS + self.URL_FORMAT_JSON)
        print(response)
        assert response.ok, f'Response not OK, status code is {response.status_code}'

        assessment_df = self.Assessments.info.df
        m_and_sq_df = assessment_df[assessment_df['Assessment Name'].str.startswith(
            ('Mission', 'Side Quest'))]
        m_and_sq_names = m_and_sq_df['Assessment Name']
        m_and_sq_map = dict(
            zip(m_and_sq_names, m_and_sq_df['Assessment ID'].astype(int)))
        submission_dfs = [self.Assessments(
            m_and_sq_map[name]).Submissions.info.df for name in m_and_sq_names]
        submission_xp_map = [dict(zip(df['User ID'], df['Exp'].fillna(
            '-').astype(str).apply(lambda x: str(int(float(x))) if x != '-' else x))) for df in submission_dfs]

        headers = ['User ID', 'Name', 'Tutors', 'Level',
                   'Exp', 'Videos Watched', 'Average % Watched', 'Phantom']

        def simplify_name(name):
            return ''.join(filter(lambda x: x.isnumeric() or x.isupper() or x == '.', name[:name.find(':')]))

        headers.extend(map(simplify_name, m_and_sq_names))

        def parse_user(user):
            user_id = int(user['nameLink'].split('/')[-1])
            name = user['name']
            if user.get('groupManagers', []):
                tutor = user.get('groupManagers')[0]['name']
            else:
                tutor = ''
            lvl = user['level']
            exp = user['experiencePoints']
            num_vids = user['videoSubmissionCount']
            avg_watched = float(user['videoPercentWatched'] or 0)
            phantom = (user['studentType'] == 'Phantom')
            assessment_xp = [xp_map.get(int(user_id), '-')
                             for xp_map in submission_xp_map]
            return [user_id, name, tutor, lvl, exp, num_vids, avg_watched, phantom, *assessment_xp]

        data = [parse_user(user) for user in response.json()['students']]
        if not self.include_phantoms:
            # Phantom column is index 7
            data = list(filter(lambda u: not u[7], data))
        return Table(headers=headers, data=data)

    @classmethod
    def flush_cache(cls):
        cls.info.fget.cache_clear()
        cls.stats.fget.cache_clear()

    @guess_id
    @lru_cache(maxsize=None)
    def __call__(self, id):
        return User(self.root, id)


class Staff(Rooted):

    URL = 'staff'
    URL_STATS = 'statistics/course/staff'

    @property
    @lru_cache(maxsize=1)
    def info(self):
        response = self.HTTP.get(self.URL + self.URL_FORMAT_JSON)
        assert response.ok, f'Response not OK, status code is {response.status_code}'

        headers = ['User ID', 'Name', 'Email',
                   'Timeline Algorithm', 'Role', 'Phantom']

        data = []
        for user in response.json()['users']:
            user_id = user['id']
            user_name = user['name']
            email = user['email']
            timeline = user.get('timelineAlgorithm')
            role = ' '.join(
                map(lambda x: x.capitalize(), user['role'].split('_')))
            is_phantom = user['phantom']
            data.append([user_id, user_name, email,
                        timeline, role, is_phantom])
        return Table(headers=headers, data=data)

    @property
    @lru_cache(maxsize=1)
    def stats(self):
        response = self.HTTP.get(self.URL + self.URL_FORMAT_JSON)
        assert response.ok, f'Info response not OK, status code is {response.status_code}'

        name_to_id_map = dict((user['name'], user['id'])
                              for user in response.json()['users'])

        response = self.HTTP.get(self.URL_STATS)
        assert response.ok, f'Stats response not OK, status code is {response.status_code}'

        headers = ['User ID', 'Name', '# Marked', '# Students',
                   'Average Time Per Assignment', 'Standard Deviation']

        data = []
        for user in response.json()['staff']:
            user_id = name_to_id_map[user['name']]
            user_name = user['name']
            num_marked = user['numGraded']
            num_students = user['numStudents']
            avg_time = user['averageMarkingTime']
            std_dev = user['stddev']
            data.append([user_id, user_name, num_marked,
                        num_students, avg_time, std_dev])
        return Table(headers=headers, data=data)

    @guess_id
    @lru_cache(maxsize=None)
    def __call__(self, id):
        return User(self.root, id)


class ExpRecords(Rooted):

    URL = 'experience_points_records'
    check_interval = 3

    @property
    @lru_cache(maxsize=1)
    def info(self):
        return self.get_info()

    def get_info(self, progress_bar=False):
        def get_data():
            i = 1
            pbar = tqdm(total=1) if progress_bar else None
            data = []
            while True:
                response = self.HTTP.get(
                    self.URL + f'?filter[page_num]={i}&format=json')
                if response.json()['records'] == []:
                    break
                i += 1
                response_json = response.json()
                if pbar is not None:
                    pbar.update(len(response_json['records'])/response_json['rowCount'])
                for experiencePointRecord in response.json()['records']:
                    record_id = experiencePointRecord['id']
                    reason = experiencePointRecord['reason']['text']
                    is_auto_disburse = experiencePointRecord['reason']['isManuallyAwarded'] == 'true'
                    submission_url = self.URL_BASE + \
                        experiencePointRecord['reason']['link'] if is_auto_disburse else ''
                    updater_id = experiencePointRecord['updater']['id']
                    updater_name = experiencePointRecord['updater']['name']
                    student_id = experiencePointRecord['student']['id']
                    student_name = experiencePointRecord['student']['name']
                    exp = experiencePointRecord['pointsAwarded']
                    timestamp = experiencePointRecord['updatedAt']
                    data.append([record_id, reason, submission_url,
                                exp, updater_id, updater_name, student_id, student_name, timestamp])
            if pbar is not None:
                pbar.close()
            return data
        headers = ['Record ID', 'Reason', 'Submission URL', 'Experience Points Awarded',
                   'Updater ID', 'Updater Name', 'User ID', 'User Name', 'Updated at']

        data = get_data()
        return Table(headers=headers, data=data)

    @property
    def info_fast(self):
        if isinstance(self, User):
            raise NotImplementedError
        download_url = self.URL + '/download' + self.URL_FORMAT_JSON
        print(download_url)
        response = self.HTTP.get(download_url)
        while True:
            response_json = response.json()
            if response_json['status'] == 'completed':
                break
            time.sleep(self.check_interval)
            response = self.HTTP.get(self.URL_BASE + response_json['jobUrl'] + self.URL_FORMAT_JSON)
        file_url = response_json['redirectUrl']
        df = pd.read_csv(file_url)
        return Table(headers=df.columns.to_list(), data=df.values.tolist())

    @guess_id
    @lru_cache(maxsize=None)
    def __call__(self, id):
        return ExpRecord(self, id)


class ExpRecord(Rooted):

    def update(self, reason='', exp=None):
        if exp is None:
            raise Exception(
                'Need to supply `exp` argument to update exp record')
        self.root.flush_cache()
        formdata = {'experience_points_record[points_awarded]': exp}
        if reason:
            formdata['experience_points_record[reason]'] = reason
        headers = {"X-Csrf-Token": self.auth_token}
        return self.HTTP.patch(self.URL + self.URL_FORMAT_JSON, data=formdata, headers=headers, allow_redirects=False)

    def delete(self):
        self.root.flush_cache()
        formdata = {
            # 'authenticity_token': self.auth_token,
            '_method': 'delete'
        }
        headers = {
            'X-CSRF-Token': self.auth_token,
        }
        return self.HTTP.post(self.URL + self.URL_FORMAT_JSON, data=formdata, headers=headers)

class PersonalTimes(Rooted):

    URL = 'personal_times'

    @property
    @lru_cache(maxsize=1)
    def info(self):
        response = self.HTTP.get(self.URL + self.URL_FORMAT_JSON)
        assert response.ok, f'Response not OK, status code is {response.status_code}'

        headers = ['Reference ID', 'Personal Times ID', 'Type', 'Title',
                   'Reference Start At', 'Reference Bonus End At', 'Reference End At',
                   'Personal Start At', 'Personal Bonus End At', 'Personal End At']
        data = []
        for ptime in response.json()['personalTimes']:
            ref_id = ptime['id']
            pt_id = ptime['personalTimeId']
            pt_type = ptime['type']
            pt_title = ptime['title']
            ref_start = ptime['itemStartAt']
            ref_bonus = ptime['itemBonusEndAt']
            ref_end = ptime['itemEndAt']
            pt_start = ptime['personalStartAt']
            pt_bonus = ptime['personalBonusEndAt']
            pt_end = ptime['personalEndAt']
            data.append([ref_id, pt_id, pt_type, pt_title,
                         ref_start, ref_bonus, ref_end,
                         pt_start, pt_bonus, pt_end])

        return Table(headers=headers, data=data)

    def recompute(self):
        formdata = {
            'utf8': '✓',
            'authenticity_token': self.auth_token,
            'commit': 'Recompute',
        }
        tgt_url = self.URL + '/recompute' + self.URL_FORMAT_JSON
        return self.HTTP.post(tgt_url, data=formdata, allow_redirects=False)
