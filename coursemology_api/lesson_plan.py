from .utility import *

print("CourseAPI.LessonPlan is not yet fixed, do not use for now.")

class LessonPlan(Rooted):

    URL = 'lesson_plan'

    @property
    @lru_cache(maxsize=1)
    def info(self):
        response = self.HTTP.get(self.URL + '/edit.json')
        json_object = json.loads(response.content)

        milestone_data = []
        for milestone in json_object['milestones']:
            milestone_data.append([
                milestone['id'],
                milestone['title'],
                milestone['description'],
                milestone['start_at']
            ])
        milestones = Table(
            headers=['ID', 'Title', 'Description', 'Start At'],
            data=milestone_data
        )

        meta = {}
        meta['milestones'] = milestones
        meta['visibilitySettings'] = json_object['visibilitySettings']
        meta['flags'] = json_object['flags']

        headers = [
            'Item Title', 'Published', 'Start At Date', 'Start At Time',
            'End At Date', 'End At Time', 'Description', 'Location',
            'Item ID', 'Event ID', 'Lesson Plan Item Type', 'Item Path',
        ]
        data = []
        for _item in json_object['items']:
            item = defaultdict(str)
            item.update(_item)
            start_at = ISODatetime(item['start_at'])
            end_at   = ISODatetime(item['end_at'])
            data.append([
                item['title'],
                item['published'],
                start_at.date(),
                start_at.time(),
                end_at.date(),
                end_at.time(),
                item['description'],
                item['location'],
                item['id'],
                item['eventId'],
                item['lesson_plan_item_type'],
                item['item_path'],
            ])

        return Table(headers=headers, data=data, meta=meta)

    def update(self, csvfilename):
        import csv
        original_df = self.info.df.astype(str).set_index('Item ID')
        with open(csvfilename, 'r', encoding='utf-8', newline='') as f:
            reader = csv.reader(f)
            headers = next(reader)
            data = [row for row in reader]
        for title, is_published, start_at_date, start_at_time, end_at_date, end_at_time, description, location, item_id, event_id, *_, item_path in data:
            changed_item_data = {}
            item_row = original_df.loc[item_id]
            item_path = item_path if item_path else f'/courses/{self.course_id}/lesson_plan/events/{event_id}'
            if title != item_row['Item Title']:
                changed_item_data['title'] = title
            if is_published  != item_row['Published']:
                changed_item_data['published'] = is_published == 'True'
            if start_at_date != item_row['Start At Date'] or start_at_time != item_row['Start At Time']:
                changed_item_data['start_at'] = ISODatetime().set_datetime(start_at_date, start_at_time)
            if end_at_date   != item_row['End At Date']   or end_at_time   != item_row['End At Time']:
                changed_item_data['end_at'] = ISODatetime().set_datetime(end_at_date, end_at_time)
            if description   != item_row['Description']: # Description has to be changed in item itself TODO: access item and modify
                changed_item_data['description'] = description
            if location      != item_row['Location']:
                changed_item_data['location'] = location
            if len(changed_item_data) > 0:
                response = self.update_item(item_path, changed_item_data)
                if response.status_code == 200:
                    print(title, item_id, "successfully modified")
                else:
                    print(title, item_id, "failed with error code", response.status_code)

    def update_item(self, item_path, item_data):
        '''Patches row_data'''
        key = item_path.split('/')[-2]
        json_key_mapping = {
            'events': 'lesson_plan_events',
            'assessments': 'assessment',
            'videos': 'video',
            'surveys': 'survey',
        }
        json_payload = {
            json_key_mapping[key]: item_data
        }
        print(self.URL_BASE + item_path + self.URL_FORMAT_JSON)
        print(json_payload)
        headers = {"X-Csrf-Token": self.auth_token}
        return self.HTTP.patch(self.URL_BASE + item_path + self.URL_FORMAT_JSON, data=None, json=json_payload, headers=headers, allow_redirects=False)
