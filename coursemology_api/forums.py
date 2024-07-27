import pandas as pd
import re
import json

from .utility import *

TOPIC_TYPES = ['normal', 'sticky', 'question', 'announcement']


class Forums(Rooted):
    URL = 'forums'

    @property
    @lru_cache(maxsize=1)
    def info(self):
        return get_default_info_table(self, records_key='forums', meta_keys=[])

    @guess_id
    @lru_cache(maxsize=None)
    def __call__(self, id):
        return Forum(self, id)

    def create(self, name, description='', forum_topics_auto_subscribe=True):
        json_payload = {
            'forum': {
                'name': name,
                'description': description,
                'forum_topics_auto_subscribe': forum_topics_auto_subscribe,
            }
        }
        headers = {"X-CSRF-Token": self.auth_token}
        self.flush_cache()
        response = self.HTTP.post(self.URL + self.URL_FORMAT_JSON, data=None, json=json_payload, headers=headers, allow_redirects=False)
        assert response.ok
        return Forum(self, response.json()['id'])


class Forum(Rooted):

    def __init__(self, root, id):
        super().__init__(root, id)
        self.Topics = Topics(self)

    @property
    @lru_cache(maxsize=1)
    def info(self):
        return get_default_info_table(self, records_key='topics', meta_keys=['forum'])

    def update(self, name, description='', forum_topics_auto_subscribe=True):
        json_payload = {
            'forum': {
                'name': name,
                'description': description,
                'forum_topics_auto_subscribe': forum_topics_auto_subscribe,
            }
        }
        headers = {"X-CSRF-Token": self.auth_token}
        return self.HTTP.patch(self.URL + self.URL_FORMAT_JSON, data=None, json=json_payload, headers=headers, allow_redirects=False)

    def delete(self):
        headers = {"X-CSRF-Token": self.auth_token}
        return self.HTTP.delete(self.URL + self.URL_FORMAT_JSON, data=None, json=None, headers=headers, allow_redirects=False)


class Topics(Rooted):
    URL = 'topics'

    @guess_id
    @lru_cache(maxsize=None)
    def __call__(self, id):
        return Topic(self, id)

    @property
    def info(self):
        return self.root.info

    def create(self, title, text, topic_type='normal', is_anonymous=False):
        assert topic_type in TOPIC_TYPES
        json_payload = {
            "topic": {
                "title": title,
                "topic_type": topic_type,
                "is_anonymous": is_anonymous,
                "posts_attributes":[
                    {"text": text, "is_anonymous": is_anonymous}
                ]
            }
        }
        headers = {"X-CSRF-Token": self.auth_token}
        response = self.HTTP.post(self.URL + self.URL_FORMAT_JSON, data=None, json=json_payload, headers=headers, allow_redirects=False)
        assert response.ok
        return Post(self, response.json()['topic']['id'])


class Topic(Rooted):
    def __init__(self, root, id):
        super().__init__(root, id)
        self.Posts = Posts(self)

    @property
    @lru_cache(maxsize=1)
    def info(self):
        return get_default_info_table(self, records_key='posts', meta_keys=['topic'])

    def update(self, title, topic_type='normal'):
        assert topic_type in TOPIC_TYPES
        json_payload = {
            "topic": {
                "id": self.id,
                "title": title,
                "topic_type": topic_type,
                "posts_attributes":[{}]
            }
        }
        headers = {"X-CSRF-Token": self.auth_token}
        return self.HTTP.patch(self.URL + self.URL_FORMAT_JSON, data=None, json=json_payload, headers=headers, allow_redirects=False)


    def delete(self):
        headers = {"X-CSRF-Token": self.auth_token}
        return self.HTTP.delete(self.URL + self.URL_FORMAT_JSON, data=None, json=None, headers=headers, allow_redirects=False)


class Posts(Rooted):
    URL = 'posts'

    @guess_id
    @lru_cache(maxsize=None)
    def __call__(self, id):
        return Post(self, id)

    @property
    def info(self):
        return self.root.info

    def create(self, text, parent=None, is_anonymous=False):
        json_payload = {
            'discussion_post': {
                'text': text,
                'parent_id': parent.id if parent is not None else None,
                'is_anonymous': is_anonymous,
            }
        }
        headers = {"X-CSRF-Token": self.auth_token}
        response = self.HTTP.post(self.URL + self.URL_FORMAT_JSON, data=None, json=json_payload, headers=headers, allow_redirects=False)
        assert response.ok
        return Post(self, response.json()['post']['id'])


class Post(Rooted):
    def __init__(self, root, id):
        super().__init__(root, id)


    def update(self, text):
        json_payload = {
            'discussion_post': {
                'text': text,
            }
        }
        headers = {"X-CSRF-Token": self.auth_token}
        return self.HTTP.patch(self.URL + self.URL_FORMAT_JSON, data=None, json=json_payload, headers=headers, allow_redirects=False)


    def delete(self):
        headers = {"X-CSRF-Token": self.auth_token}
        return self.HTTP.delete(self.URL + self.URL_FORMAT_JSON, data=None, json=None, headers=headers, allow_redirects=False)
