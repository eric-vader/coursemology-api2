from .utility import *

class Levels(Rooted):

    URL = 'levels'

    @property
    @lru_cache(maxsize=1)
    def info(self): # CourseAPI(course_id).Levels.info
        '''
        Returns information about the exp to reach each level in current course.
        '''
        response = self.HTTP.get(self.URL + self.URL_FORMAT_JSON)
        json_object = json.loads(response.content)
        levels = json_object['levels']
        meta = {'can_manage': json_object['canManage']}

        headers = ['Level', 'Min Exp']
        data = []
        for lvl, min_exp in enumerate(levels):
            data.append([lvl, min_exp])
        return Table(headers=headers, data=data, meta=meta)

    def update(self, levels_dict):
        '''Updates the levels using the dictionary {lvl: min_exp, ...}'''
        original_levels_dict = dict(self.info.data)
        original_levels_dict.update(levels_dict)
        items0 = sorted(original_levels_dict.items(), key=lambda item: item[0])
        items1 = sorted(original_levels_dict.items(), key=lambda item: item[1])
        assert items0 == items1, 'EXP for levels must be strictly increasing'
        try:
            levels = [original_levels_dict[lvl] for lvl in range(max(original_levels_dict) + 1)]
        except KeyError:
            raise Exception(f'Level {level} missing')
        json_payload = {
            'levels': levels,
        }
        headers = {"X-Csrf-Token": self.auth_token}
        self.flush_cache()
        return self.HTTP.post(self.URL + self.URL_FORMAT_JSON, data=None, json=json_payload, headers=headers, allow_redirects=False)

    def flush_cache(self):
        self.__class__.info.fget.cache_clear()
