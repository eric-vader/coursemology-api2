import dataclasses
import json
import requests
import time
import re
import os
import csv
import pandas as pd

from functools import lru_cache
from dateutil import tz, parser
from datetime import datetime, timezone, timedelta
from getpass import getpass
from collections.abc import MutableMapping

from .auth import authenticate

from .config import COOKIE_FILENAME, LOGIN_FILENAME

@dataclasses.dataclass
class WithContext:
    course: object
    current_value: bool = False

    def __enter__(self):
        try:
            self.old_value = self.current_value
            self.current_value = self.new_value
            del self.new_value
        except AttributeError:
            raise Exception('Use with-statement in this way:\nwith course.attribute(tmp_value):\n\t...more code here...')

    def __exit__(self, exception_type, exception_value, traceback):
        self.current_value = self.old_value
        del self.old_value

    def __bool__(self):
        return bool(self.current_value)

    def __repr__(self):
        return str(self.current_value)

    def __call__(self, new_value=True):
        self.new_value = new_value
        return self

@dataclasses.dataclass
class Table:
    headers: list
    data: list
    meta: dict = dataclasses.field(default_factory=dict)

    @property
    @lru_cache(maxsize=1)
    def df(self):
        return pd.DataFrame(self.data, columns=self.headers)

    def to_csv(self, filename):
        with open(filename, 'w', encoding='utf-8', newline='') as out:
            writer = csv.writer(out)
            writer.writerow(self.headers)
            writer.writerows(self.data)

    def __repr__(self):
        return self.df.to_string(index=False)

    def __hash__(self):
        return id(self)

class Rooted:
    def __init__(self, root, id=None, skip_url=False):
        self.root = root
        self.skip_url = skip_url
        if id is not None:
            self.id = id
            self.URL = root.URL + f'/{id}'

    def __getattribute__(self, name):
        try:
            result = super().__getattribute__(name)
            if name[:3] == 'URL':
                root = self.root.root if self.skip_url else self.root
                if result[:len(root.URL)] != root.URL:
                    return root.URL + '/' + result
        except AttributeError:
            result = self.root.__getattribute__(name)
        return result

    @property
    def name_to_id(self):
        return {row[index_of_first_string(row)]: row[0] for row in self.info.data}

    def flush_cache(self):
        try:
            self.__class__.info.fget.cache_clear()
            self.__class__.stats.fget.cache_clear()
        except AttributeError:
            pass
        except Exception as e:
            print("error while clearing cache", e)

def redirect(request_method):
    def helper(self, *args, **kwargs):
        response = request_method(self, *args, **kwargs)
        if response.status_code == 401:
            print("=== Coursemology sign-in required ===")
            os.makedirs(os.path.dirname(LOGIN_FILENAME), exist_ok=True)
            validLogin = os.path.exists(LOGIN_FILENAME) and kwargs.get('tag') != 'retry_sign_in'
            if validLogin:
                print('Reading cached login particulars...')
                try:
                    login_data = json_load(LOGIN_FILENAME)
                    username, password = login_data['username'], login_data['password']
                except:
                    validLogin = False
            if not validLogin:
                print('Requesting login particulars...')
                username = input('username: ')
                password = getpass('password: ')
                json_save(LOGIN_FILENAME, {
                    'username': username,
                    'password': password
                })
            print("Logging in...")
            token, cookies = authenticate(username, password)
            for cookie in cookies:
                self.session.cookies.set(cookie['name'], cookie['value'])
            self.dump_cookies()
            response = request_method(self, *args, **kwargs)
        if response.status_code == 202:
            print('Processing job... Retrying in 2 seconds.')
            time.sleep(2)
            response = redirect(request_method)(self, *args, **kwargs)
        return response
    return helper

class HTTP(Rooted):

    VALID_STATUS_CODES = {200, 201, 202, 302}

    def __init__(self, root, cookie_path):
        self.cookie_path = cookie_path
        self.session = requests.Session()
        self.load_cookies()
        super().__init__(root)

    def load_cookies(self):
        if os.path.isfile(self.cookie_path):
            cookie_jar = requests.utils.cookiejar_from_dict(json_load(self.cookie_path))
            self.session.cookies.update(cookie_jar)

    def dump_cookies(self):
        # Just in case it's needed, this can be a rather quick lookup
        self.cookie_dict = self.session.cookies.get_dict()
        json_save(self.cookie_path, self.cookie_dict)

    @redirect
    def get(self, url, data=None, **kwargs):
        response = self.session.get(url, data=data, **kwargs)
        return self.with_warning(response)

    @redirect
    def post(self, url, data, tag=None, **kwargs):
        response = self.session.post(url, data=data, **kwargs)
        return self.with_warning(response)

    @redirect
    def patch(self, url, data, **kwargs):
        response = self.session.patch(url, data=data, **kwargs)
        return self.with_warning(response)

    @redirect
    def put(self, url, data, **kwargs):
        response = self.session.put(url, data=data, **kwargs)
        return self.with_warning(response)

    @redirect
    def delete(self, url, data=None, **kwargs):
        response = self.session.delete(url, data=data, **kwargs)
        return self.with_warning(response)

    @staticmethod
    def with_warning(response):
        if response.status_code not in HTTP.VALID_STATUS_CODES:
            print("WARNING! Invalid status code:", response.status_code, response.url)
        return response

class ISODatetime:
    def __init__(self, iso_string=''):
        self.datetime = parser.parse(iso_string).replace(microsecond=0) if iso_string else ''
    def set_datetime(self, date_str, time_str):
        dt = datetime.strptime(date_str + time_str, '%Y-%m-%d%H:%M:%S')
        self.datetime = dt.astimezone(tz.tzlocal())
        return self
    def date(self):
        return self.datetime.date() if self.datetime else ''
    def time(self):
        return self.datetime.time() if self.datetime else ''
    def __str__(self):
        if type(self.datetime) == datetime:
            dt = self.datetime.astimezone(timezone.utc)
            return f'{dt.date()}T{dt.time()}.000Z'
        return ""
    def __repr__(self):
        return str(self)
    def __add__(self, other):
        assert type(other) == timedelta, "Use a datetime.timedelta object"
        return ISODatetime((self.datetime + other).isoformat())

illegal_chars = re.compile("[^a-zA-Z0-9]+")
def str2path(string):
    return illegal_chars.sub(' ', string).strip().replace(' ', '_').lower()

def guess_id(getter):
    def guesser(self, *args, **kwargs):
        if 'id' in kwargs:
            return getter(self, id=kwargs.pop('id'))
        if args and type(args[0]) == int:
            return getter(self, id=args[0])
        if 'name' in kwargs and kwargs['name'] in self.name_to_id:
            return getter(self, id=self.name_to_id[kwargs.pop('name')])
        if args and args[0] in self.name_to_id:
            return getter(self, id=self.name_to_id[args[0]])
        if args and args[0] in self.name_to_id.values():
            return getter(self, id=args[0])
        raise Exception(f"Given `id` or `name` does not exist: {args if args else ''}{kwargs if kwargs else ''}")
    return guesser

def get_question_id(instance, question, idx=0):
    question_ids = [row[idx] for row in instance.info.data]
    question_id  =  question_ids[0]                 if question == 'first' else \
                    question_ids[-1]                if question == 'last' else \
                    question                        if str(question) in question_ids else \
                    question_ids[question - 1]      if type(question) == int and 0 < question <= len(question_ids) else \
                    question_ids[int(question) - 1] if question.isdigit() and 0 < int(question) <= len(question_ids) else \
                    question
    if question_id is None:
        raise ValueError('Invalid question selected. Try question="first", question="last", or question=2 for second question.')
    return question_id


def json_save(path, data):
    with open(path, 'w') as f:
        data = json.dump(data, f)

def json_load(path):
    with open(path, 'r') as f:
        return json.load(f)

# Source: https://stackoverflow.com/a/6027615
def flatten_dictionary(dictionary, parent_key='', separator='_'):
    items = []
    for key, value in dictionary.items():
        new_key = parent_key + separator + key if parent_key else key
        if isinstance(value, MutableMapping):
            items.extend(flatten_dictionary(value, new_key, separator=separator).items())
        else:
            items.append((new_key, value))
    return dict(items)

def records_to_df(records):
    assert len(records) > 0, "Records can't be empty"

    records = [flatten_dictionary(record, separator=': ') for record in records]

    df = pd.DataFrame.from_records(records)

    mapping = {col:re.sub(r'(?<=[a-z])(?=[A-Z])', ' ', col).title() for col in df.columns}
    mapping['id'] = 'ID'

    df = df.rename(columns=mapping)

    return df

def get_default_info_table(instance, records_key=None, meta_keys=[], url=None):
    response = instance.HTTP.get((instance.URL + instance.URL_FORMAT_JSON) if url is None else url)
    assert response.ok, f'Response not OK, status code is {response.status_code}'
    response_json = response.json()
    meta = {k:response_json[k] for k in meta_keys}
    records = response_json[records_key]
    if len(records) == 0:
        return None

    df = records_to_df(records)

    return Table(headers=df.columns.to_list(), data=df.values.tolist(), meta=meta)

def index_of_first_string(lst):
    for i, val in enumerate(lst):
        if isinstance(val, str):
            return i
    raise Exception('Not found')
