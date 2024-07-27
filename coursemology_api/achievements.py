from .utility import *

class Achievements(Rooted):

    URL = 'achievements'

    @property
    @lru_cache(maxsize=1)
    def info(self):
        response = self.HTTP.get(self.URL + self.URL_FORMAT_JSON, headers={'X-Csrf-Token': self.auth_token})
        headers = ['Achievement ID', 'Name', 'Description']
        data = []
        for achievement in response.json()['achievements']:
            achievement_id = achievement['id']
            achievement_name = achievement['title']
            description = achievement['description']
            data.append([achievement_id, achievement_name, description])
        return Table(headers=headers, data=data)

    @guess_id
    @lru_cache(maxsize=None)
    def __call__(self, id):
        return Achievement(self, id)

class Achievement(Rooted):
    @property
    @lru_cache(maxsize=1)
    def info(self):
        response = self.HTTP.get(self.URL + self.URL_FORMAT_JSON, headers={'X-Csrf-Token': self.auth_token})
        headers = ['Student ID', 'Student Name']
        data = []
        for student in response.json()['achievement']['achievementUsers']:
            data.append([student['id'], student['name']])
        return Table(headers=headers, data=data)

    def award(self, student_ids=[], keep_existing=True):
        formdata = {
            'utf8': '✓',
            '_method': 'patch',
            'authenticity_token': self.auth_token,
            'commit': 'Update Users',
        }
        formdata  = tuple(formdata.items())
        key = 'achievement[course_user_ids][]'
        if keep_existing:
            student_ids = set(student_ids).union({row[0] for row in self.info.data})
        formdata += tuple((key, user_id) for user_id in student_ids)
        return self.HTTP.post(self.URL, data=formdata, allow_redirects=False, headers={'X-Csrf-Token': self.auth_token})