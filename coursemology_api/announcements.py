from .utility import *

class Announcements(Rooted):

    URL = 'announcements'

    @property
    @lru_cache(maxsize=1)
    def info(self):
        response = self.HTTP.get(self.URL + self.URL_FORMAT_JSON)
        headers = ['Announcement ID', 'Title', 'Start Date', 'End Date', 'Content']
        data = []
        for announcement in response.json()['announcements']:
            announcement_id = announcement['id']
            announcement_title = announcement['title']
            start_at = announcement['startTime']
            end_at = announcement['endTime']
            content = announcement['content']
            data.append([announcement_id, announcement_title, start_at, end_at, content])
        return Table(headers=headers, data=data)

    def create(self, title, html_content, start_at=None, end_at=None, duration=None, is_sticky=False):
        formdata = {
            'utf8': '✓',
            '_method': 'post',
            'authenticity_token': self.auth_token,
            'commit': 'Create Announcement',
        }
        assert (end_at is None) ^ (duration is None), "Either end_at or duration has to be set, but not both."
        if start_at is None:
            start_at = ISODatetime(datetime.now(tz=tz.tzlocal()).isoformat())
        if duration:
            end_at = start_at + duration
        formdata['announcement[title]'] = title
        formdata['announcement[content]'] = html_content
        formdata['announcement[start_at]'] = start_at
        formdata['announcement[end_at]'] = end_at
        formdata['announcement[sticky]'] = int(is_sticky)
        response = self.HTTP.post(self.URL + self.URL_FORMAT_JSON, data=formdata, allow_redirects=False)
        return response # TODO: redirects to announcement page, so announcement ID has to be manually retrieved

    @guess_id
    @lru_cache(maxsize=None)
    def __call__(self, id):
        return Announcement(self, id)

class Announcement(Rooted):
    @property
    @lru_cache(maxsize=1)
    def info(self):
        pass # TODO: Think about what kind of info to return. Blank table but with meta?

    def update(self, title=None, html_content=None, start_at=None, end_at=None, duration=None, is_sticky=False):
        # TODO: Test this. Not yet tested.
        assert end_at is None or duration is None, "Cannot set both end_at and duration at the same time."
        if duration:
            # TODO: get the start_at from info
            end_at = start_at + duration
        formdata = {
            'utf8': '✓',
            '_method': 'post',
            'authenticity_token': self.auth_token,
            'commit': 'Update Announcement',
        }
        if title: formdata['announcement[title]'] = title
        if html_content: formdata['announcement[content]'] = html_content
        if start_at: formdata['announcement[start_at]'] = start_at
        if end_at: formdata['announcement[end_at]'] = end_at
        if is_sticky: formdata['announcement[sticky]'] = is_sticky
        return self.HTTP.patch(self.URL + '?format=json', data=formdata, allow_redirects=False)
    
    def delete(self):
        formdata = {
            'authenticity_token': self.auth_token,
            '_method': 'delete'
        }
        return self.HTTP.delete(self.URL + '?format=json', data=formdata, allow_redirects=False)