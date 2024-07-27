from .utility import *

class Groups(Rooted):

    URL = 'groups'

    @property
    @lru_cache(maxsize=1)
    def info(self): # CourseAPI(course_id).Groups.info
        '''
        Returns information about the groups in current course.
        '''
        response = self.HTTP.get(self.URL + self.URL_FORMAT_JSON)
        assert response.ok

        headers = ['Group ID', 'Name', 'Members',
                   'Phantom', 'Total', 'Managers', 'Category ID', 'Category Name']
        data = []

        for category in response.json()['groupCategories']:
            cat_id = category['id']

            inner_response = self.HTTP.get(f'{self.URL}/{cat_id}/info' + self.URL_FORMAT_JSON)
            assert inner_response.ok

            groups = inner_response.json()['groups']
            cat_name = inner_response.json()['groupCategory']['name']
            for group in groups:
                gid, name, all_members = group['id'], group['name'], group['members']
                total = len(all_members)
                members = [member['name'] for member in all_members if member['groupRole'] == 'normal']
                phantom = [member['name'] for member in all_members if member['isPhantom']]
                managers = [member['name'] for member in all_members if member['groupRole'] == 'manager']
                data.append([gid, name, members, phantom, total, managers, cat_id, cat_name])

        return Table(headers=headers, data=data)

    def create(self, student_ids, tutor_ids, group_name, category_name, description=None):
        response = self.HTTP.get(self.URL + self.URL_FORMAT_JSON)
        assert response.ok

        cat_id = None
        for group_cat in response.json()['groupCategories']:
            if group_cat['name'] == category_name:
                cat_id = group_cat['id']
                break

        if cat_id == None:
            # Create new category and run the function again
            self.create_category(category_name)
            return self.create(student_ids, tutor_ids, group_name, category_name, description)

        headers = {"X-Csrf-Token": self.auth_token}
        json_payload = {'groups': [{'name': group_name, 'description': description}]}
        self.flush_cache()
        response = self.HTTP.post(f'{self.URL}/{cat_id}/groups{self.URL_FORMAT_JSON}', data=None, json=json_payload, headers=headers, allow_redirects=False)
        assert response.ok

        try:
            group_id = response.json()['groups'][0]['id']
        except IndexError:
            raise Exception('Group creation failed, group may have existed!')
        group = self(id=group_id)
        group.update(student_ids, tutor_ids=tutor_ids, group_name=group_name, description=description)
        return group

    def create_category(self, category_name, description=None):
        '''
        Creates a category with a given category name and an optional description.
        '''
        headers = {"X-Csrf-Token": self.auth_token}
        json_payload = {'name': category_name, 'description': description}
        self.flush_cache()
        return self.HTTP.post(f'{self.URL}{self.URL_FORMAT_JSON}', data=None, json=json_payload, headers=headers, allow_redirects=False)

    def delete(self, category_id):
        '''
        Deletes a group category.
        '''
        headers = {"X-Csrf-Token": self.auth_token}
        return self.HTTP.delete(f'{self.URL}/{category_id}{self.URL_FORMAT_JSON}', headers=headers)

    @guess_id
    @lru_cache(maxsize=None)
    def __call__(self, id):
        return Group(self, id)

class Group(Rooted):

    ROLE_STUDENT = 'Student'
    ROLE_STAFF = 'Manager'

    @property
    @lru_cache(maxsize=1)
    def info(self):
        '''
        Returns information about this group.
        '''
        parent_info_df = self.root.info.df
        try:
            filtered_df = parent_info_df[parent_info_df['Group ID'] == self.id].iloc[0]
        except:
            raise Exception('Cannot find group with the given ID!')

        headers = ['User ID', 'Name', 'Role']
        data = []
        cat_id = filtered_df['Category ID']

        response = self.HTTP.get(f'{self.root.URL}/{cat_id}/info' + self.URL_FORMAT_JSON)
        assert response.ok

        groups = response.json()['groups']
        for group in groups:
            gid, all_members = group['id'], group['members']
            if gid == self.id:
                for member in all_members:
                    if member['groupRole'] == 'manager':
                        data.append([member['id'], member['name'], self.ROLE_STAFF])
                    else:
                        data.append([member['id'], member['name'], self.ROLE_STUDENT])
        return Table(headers=headers, data=data)

    def update(self, student_ids, tutor_ids=[], group_name=None, description=None):
        '''
        Updates the particulars of a specific group.
        '''
        parent_info_df = self.root.info.df
        try:
            filtered_df = parent_info_df[parent_info_df['Group ID'] == self.id].iloc[0]
        except:
            raise Exception('Cannot find group with the given ID!')

        headers = {"X-Csrf-Token": self.auth_token}
        cat_id = filtered_df['Category ID']

        # Update group name and description
        json_payload = {
            'name': group_name,
            'description': description
        }
        self.flush_cache()
        response = self.HTTP.patch(f'{self.root.URL}/{cat_id}/groups/{self.id}{self.URL_FORMAT_JSON}', data=json_payload, headers=headers, allow_redirects=False)
        assert response.ok

        # Update group members
        json_payload = {'groups': [{
            'id': self.id,
            'name': group_name,
            'description': description,
            'members': []
        }]}

        for student_id in student_ids:
            json_payload['groups'][0]['members'].append({
                'id':           student_id,
                'role':         'normal',
                'groupRole':    'normal'
            })
        for tutor_id in tutor_ids:
            json_payload['groups'][0]['members'].append({
                'id':           tutor_id,
                'role':         'manager',
                'groupRole':    'manager'
            })

        self.flush_cache()
        return self.HTTP.patch(f'{self.root.URL}/{cat_id}/group_members' + self.URL_FORMAT_JSON, data=None, json=json_payload, headers=headers, allow_redirects=False)

    def delete(self):
        '''
        Deletes the group.
        '''
        parent_info_df = self.root.info.df
        try:
            filtered_df = parent_info_df[parent_info_df['Group ID'] == self.id].iloc[0]
        except:
            raise Exception('Cannot find group with the given ID!')

        headers = {"X-Csrf-Token": self.auth_token}
        cat_id = filtered_df['Category ID']
        return self.HTTP.delete(f'{self.root.URL}/{cat_id}/groups/{self.id}{self.URL_FORMAT_JSON}', headers=headers)