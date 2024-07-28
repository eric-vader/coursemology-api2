import json
import os
import re
import pathlib
from functools import lru_cache
from collections import defaultdict

from .config import COOKIE_FILENAME

from .utility import *
from .achievements import Achievements
from .assessments import Assessments, Assessment
from .groups import Groups, Group
from .surveys import Surveys, Survey
from .users import Users, User, Students, Staff, ExpRecords, ExpRecord, PersonalTimes
from .lesson_plan import LessonPlan
from .announcements import Announcements
from .levels import Levels
from .forums import Forums

class CourseAPI:

    URL_BASE        = f'https://coursemology.org'
    URL_AUTH_CHECK  = f'{URL_BASE}/user/profile/edit'
    URL_FORMAT_JSON = f'?format=json'

    def __init__(self, course_id):
        self.URL = self.URL_BASE + f'/courses/{course_id}'

        self.course_id = course_id
        self.root = self

        self.include_phantoms = WithContext(self, False)
        self.include_all_assessments = WithContext(self, False)
        self.include_submissions_breakdown = WithContext(self, False)

        self.HTTP = HTTP(self, COOKIE_FILENAME)
        self.Achievements  = Achievements(self)
        self.Groups        = Groups(self)
        self.Surveys       = Surveys(self)
        self.Users         = Users(self)
        self.Assessments   = Assessments(self)
        self.LessonPlan    = LessonPlan(self)
        self.Announcements = Announcements(self)
        self.Levels        = Levels(self)
        self.Forums        = Forums(self)
        self.ExpRecords    = ExpRecords(self)
        self.Workbin       = None
        self.Notifications = None

    def login(self):
        response = self.HTTP.get(self.URL_AUTH_CHECK)
        print("Success, you logged in to Coursemology successfully.")
        return self

    @property
    @lru_cache(maxsize=1)
    def info(self):
        response = self.HTTP.get(self.URL + self.URL_FORMAT_JSON)
        return response.json()['course']

    def upload(self, filepath):
        filepath = pathlib.Path(filepath)
        with open(filepath, 'rb') as f:
            filedata = f.read()
        files = {'file': filedata}
        data = {'name': filepath.name}
        headers = {"X-Csrf-Token": self.auth_token}
        resp = self.HTTP.post(self.URL_BASE + '/attachments', data=data, files=files, headers=headers)
        json_obj = resp.json()
        assert json_obj['success'], f"Upload failed: {filepath}"
        return '/attachments/' + json_obj['id']

    @property
    @lru_cache(maxsize=1)
    def auth_token(self):
        response = self.HTTP.get(self.URL_BASE + '/csrf_token' + self.URL_FORMAT_JSON)
        return response.json()['csrfToken']

    def __setattr__(self, name, value):
        if hasattr(self, name) and isinstance(self.__getattribute__(name), WithContext):
            super().__setattr__(name, WithContext(self, value))
        else:
            super().__setattr__(name, value)
