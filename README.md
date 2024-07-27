# Coursemology API

## Install
```
pip install -e .
```

## Contents
- [Coursemology API](#coursemology_api)
    - [`CourseAPI`](#courseapi)
    - [`Achievements`](#achievements)
    - [`Announcements`](#announcements)
    - [`Assessments`](#assessments)
    - [`Groups`](#groups)
    - [`LessonPlan`](#lessonplan)
    - [`Levels`](#levels)
    - [`Users`](#users)
    - [Utility](#utility)
        - [`WithContext`](#withcontext)
        - [`Table`](#table)
        - [`Rooted`](#rooted)
        - [`HTTP`](#http)
        - [`ISODatetime`](#isodatetime)
        - [`redirect`](#redirect)
        - [`guess_id`](#guess_id)
        - [`get_question_id`](#get_question_id)


## [Coursemology API](coursemology_api)

### [`CourseAPI`](coursemology_api/course.py)

[Back to top](#api)

##### Constructor

- `CourseAPI(course_id)`

    Creates a `CourseAPI` object with the given course ID.

    Parameter(s):
    - `course_id`: The course ID as an integer.

##### Properties

- `course.URL`

    The course-specific URL.

- `course.course_id`

    The course ID as an integer.

- `course.auth_token`

    CSRF token for HTTP POST requests. Dynamic property.

- `course.HTTP`

    HTTP instance for dealing with requests.

##### Methods

- `course.login()`

    Attempts to login to the course with the given course ID.

- `course.upload(filepath)`

    Uploads an attachment into the course.
    
    Parameter(s):
    - `filepath`: The filepath as a string.

##### Example

```py
from coursemology_api import CourseAPI
course = CourseAPI(2352)
course.login()
```

### [`Achievements`](coursemology_api/achievements.py)

[Back to top](#api)

##### Constructor

- `course.Achievements`

    Represents the `Achievements` instance attributed to the course.

- `course.Achievements(achievement_id)`

    Represents a specific `Achievement` instance with the given `achievement_id`.

    Parameter(s):
    - `achievement_id`: The achievement ID as an integer.

- `course.Achievements(achievement_name)`

    Represents a specific `Achievement` instance with the given `achievement_name`.

    Parameter(s):
    - `achievement_name`: The achievement name as a string.

##### Properties

- `achievements.URL`

    The URL to the list of achievements.

- `achievements.info`

    Returns a `Table` of achievements. Each row contains an achievement ID, achievement name, and achievement description.

- `achievement.URL`

    The URL to a specific achievement.

- `achievement.info`

    Returns a `Table` of achievement holders. Each row contains a student ID and the student name.

##### Methods

- `achievement.award(student_ids, keep_existing=True)`

    Awards this achievement to the students given by their student IDs. Optional to determine whether the awarding completely overwrites the existing achievement holder(s).

    Parameter(s):
    - `student_ids`: The list of student IDs as integers.
    - `keep_existing`: A boolean to determine whether to keep existing achievement holders. Set by default to `True`.

##### Example

```py
from coursemology_api import CourseAPI
course = CourseAPI(2352)

# Use .df attribute to convert to DataFrame
achievements_df = course.Achievements.info.df
ocd_df = course.Achievements(14268).info.df

# Award forum sage
course.Achievements(14214).award(student_ids=[50000, 50001], keep_existing=True)
```

### [`Announcements`](coursemology_api/announcements.py)

[Back to top](#api)

##### Constructor

- `course.Announcements`

    Represents the `Announcements` instance attributed to the course.

- `course.Announcements(announcement_id)`

    Represents a specific `Announcement` instance with the given `announcement_id`.

    Parameter(s):
    - `announcement_id`: The announcement ID as an integer.

- `course.Announcements(announcement_name)`

    Represents a specific `Announcement` instance with the given `announcement_name`.

    Parameter(s):
    - `announcement_name`: The announcement name as a string.

##### Properties

- `announcements.URL`

    The URL to the list of announcements.

- `announcements.info`

    Returns a `Table` of announcements. Each row contains:
    - an announcement ID
    - the announcement title
    - announcement start date
    - announcement end date
    - announcement content in HTML form

##### Methods

- `announcements.create(title, html_content, start_at=None, end_at=None, duration=None, is_sticky=False)`

    Creates an announcement with the specified title, content, optional start date, optional end date, optional duration, and whether the announcement is sticky or not.

    **Note that only exactly one between `end_at` and `duration` must be provided.**

    Parameter(s):
    - `title`: The announcement title string.
    - `html_content`: The content as a HTML string.
    - `start_at`: [An `ISODatetime` object](#utility-isodatetime) specifying the start time of the announcement. If not provided, it will take the current timestamp.
    - `end_at`: [An `ISODatetime` object](#utility-isodatetime) specifying the end time of the announcement. If not provided, it will take the start time added by the duration.
    - `duration`: [A `datetime.timedelta` object](https://docs.python.org/3/library/datetime.html#timedelta-objects) specifying the duration of this announcement. Overwrites `end_at` if this parameter is provided.
    - `is_sticky`: A boolean whether this announcement should be sticky. Here, "sticky" means that the announcement will remain at the top of the announcements page. Set by default to `False`.

- `announcement.delete()`

    Deletes the announcement with the given `announcement_id`.

##### Example

```py
from coursemology_api import CourseAPI, ISODatetime
from datetime import timedelta
course = CourseAPI(2352)

title = 'Test if you have COVID+'
content = '<p>Please inform us if you are COVID+</p>'
start_date = ISODatetime('2022-12-19T10:30:00.000+08:00') # 19 December 2022, 10:30 AM GMT+8
end_date = ISODatetime('2022-12-24T23:30:00.000+08:00') # 24 December 2022, 11:30 PM GMT+8
duration = timedelta(days=31) # 31 days

# List of announcements
# Use .df to convert to DataFrame
course.Announcements.info.df

# Sticky announcement from 19-24 December 2022
course.Announcements.create(title, content, start_at=start_date, end_at=end_date, is_sticky=True)

# Normal announcement from 19 December 2022 - 19 January 2023
course.Announcements.create(title, content, start_at=start_date, duration=duration)

# Normal announcement from now until next 31 days
course.Announcements.create(title, content, duration=duration)

# Normal announcement from now until 24 December 2022
course.Announcements.create(title, content, end_at=end_date)

# Delete an announcement
course.Announcements(6123).delete()
```

### [`Assessments`](coursemology_api/assessments.py)

[Back to top](#api)

##### Constructor

- `course.Assessments`

    Represents the `Assessments` instance attributed to the course.

- `course.Assessments(assessment_id)`

    Represents a specific `Assessment` instance with the given `assessment_id`.

    Parameter(s):
    - `assessment_id`: The assessment ID as an integer.

- `course.Assessments(assessment_name)`

    Represents a specific `Assessment` instance with the given `assessment_name`.

    Parameter(s):
    - `assessment_name`: The assessment name as a string.

- `course.Assessments(assessment_id_or_assessment_name).Submissions`

    Represents a specific `Submissions` instance of an assessment with the given `assessment_id` or `assessment_name`.

    Parameter(s):
    - Either one of the following:
        - `assessment_id`: The assessment ID as an integer.
        - `assessment_name`: The assessment name as a string.

- `course.Assessments(assessment_id_or_assessment_name).Submissions(submission_id_or_student_name)`

    Represents a specific `Submission` instance of a submission with the given `submission_id` or `student_name` of an assessment with the given `assessment_id` or `assessment_name`.

    Parameter(s):
    - Either one of the following:
        - `assessment_id`: The assessment ID as an integer.
        - `assessment_name`: The assessment name as a string.
    - Either one of the following:
        - `submission_id`: The submission ID as an integer.
        - `student_name`: The student name as a string.

##### Properties

- `assessments.URL`

    The URL to the list of assessments.

- `assessments.URL_ADMIN`

    The URL to the assessment settings. Only course managers can access.

- `assessments.info`

    Returns a `Table` of the assessments list. Depending on the context, this table may include all assessments or just the ones on the main page. See the example run for more reference.

    Each row contains:
    - the assessment ID
    - the assessment name
    - whether the assessment has personal times
    - whether the assessment affects personal times
    - whether the assessment is draft or published
    - whether the assessment has a password, usually for PE
    - the base EXP it has, if any
    - the bonus EXP it has, if any
    - achievements this assessment is a requirement for
    - start time of this assessment
    - bonus end time of this assessment (completing the assessment beyond this time will not award the student the bonus EXP)
    - end time of this assessment
    - category ID of the assessment
    - category name of the assessment
    - tab ID of the assessment
    - tab name of the assessment

- `assessment.info`

    Returns a `Table` of the questions on the assessment. Each row contains:
    - the question ID
    - the question name
    - the question type
    - the question URL

    The metadata contains:
    - the assessment ID
    - the assessment name
    - the assessment type, e.g. "Autograded Assessment"
    - the base EXP the assessment has
    - the bonus EXP the assessment has
    - the start time of the assessment
    - the bonus end time of the assessment
    - the end time of the assessment
    - the graded test case types of the assessment
    - the list of pairs `(filename, URL)`

- `submissions.URL`

    The URL to all submissions of the course.

- `submissions.URL_STATS`

    The URL to download the statistics of the submissions as a JSON file.

- `submissions.info`

    Returns a `Table` of the submissions list. Each row contains:
    - the submission ID
    - the user name
    - the user ID
    - whether the user is a student or not
    - submission status: either one of `unstarted`, `attempting`, `submitted`, `published`
    - the grade of the submission
    - the maximum grade attainable from the assessment
    - the EXP obtained from the submission
    - submitted time of the submission
    - graded time of the submission
    - whether the user is a phantom or not

    The metadata contains:
    - the ID of the assessment associated with the submissions
    - the assessment name
    - the maximum grade attainable from this assessment

- `submissions.stats`

    Returns a `Table` of the submissions statistics. Each row contains:
    - the user name
    - whether the user is a phantom or not
    - submission status: either one of `attempting`, `submitted`, `published`
    - the grade of the submission
    - the maximum grade attainable from the assessment
    - the EXP obtained from the submission
    - attempted time of the assessment
    - submitted time of the submission
    - time taken to submit after attempting the assessment
    - graded time of the submission
    - time taken to grade the submission
    - grader(s) of the submission
    - grade publisher of the submission

- `submission.info`

    Returns a `Table` of the submission data. Each row contains:
    - the submission question ID
    - the question name
    - the question ID
    - the question duplication ID
    - the question type
    - the answer ID
    - the actual answer (code)
    - the answer meta info
    - grade obtained from this question
    - maximum grade attainable from this question
    - test cases passed, in the form of `public;private;evaluation`
    - test cases count, in the form of `public;private;evaluation`
    - time of submission creation

    The metadata is the same as the metadata of `assessment.info` with some additional information:
    - the assessment category ID
    - the assessment tab ID
    - the status of this submission
    - the student name associated with this submission as a dictionary `{'name': str, 'id': int}`
    - grader name, if any
    - the time this assessment is attempted by the student, if attempted
    - the time this assessment is submitted by the student, if submitted
    - the time this assessment is graded by the grader, if graded
    - the grade obtained and maximum grade of this assessment
    - the awarded EXP from this submission
    - whether this submission is late or not
    - whether to show output
    - whether to show error log

##### Methods

- `assessment.download(directory=None)`

    Downloads both file attachments and test packages into `directory`.

    Parameter(s):
    - `directory`: The directory string. If not specified, it will save it to the corresponding course ID folder inside the `data` directory.

- `assessment.download_files(directory=None)`

    Downloads assessment file attachments into `directory`.

    Parameter(s):
    - `directory`: The directory string. If not specified, it will save it to the corresponding course ID folder inside the `data` directory.

- `assessment.download_tests(directory=None)`

    Downloads the test packages into `directory`.

    Parameter(s):
    - `directory`: The directory string. If not specified, it will save it to the corresponding course ID folder inside the `data` directory.

- `assessment.move(target_tab_id)`

    Moves an assessment from its tab ID to another specified `target_tab_id`.

    Parameter(s):
    - `target_tab_id`: The destination tab ID as an integer.

- `assessment.publish()`

    Publishes the assessment, if unpublished.

- `assessment.unpublish()`

    Unpublishes the assessment, if published.

- `assessment.skippable(is_skippable)`

    Sets the assessment questions to be skippable/unskippable.

    Parameter(s):
    - `is_skippable`: A boolean specifying if the assessment questions are skippable or not.

- `assessment.duplicate(question, assessment_id_or_name)`

    Duplicates a `question` to another assessment given by the `assessment_id` or `assessment_name`. See [`get_question_id`](#get_question_id) to see how the `question` variable is defined.

    Parameter(s):
    - `question`: A string or integer.
    - Either one of the following:
        - `assessment_id`: The assessment ID as an integer.
        - `assessment_name`: The assessment name as a string.

- `assessment.delete()`

    Deletes the assessment. There's no going back, use this wisely!

- `submissions.download(directory=None, max_workers=None)`

    Downloads all **graded** submissions of an assessment into `directory`. As there can be so many submissions, a concurrent job is needed, specified using `max_workers` workers.

    Parameter(s):
    - `directory`: The directory string. If not specified, it will save it to the corresponding course ID folder inside the `data` directory.
    - `max_workers`: An integer specifying how many workers needed for the concurrent job to run.

- `submission.download(filename=None, directory=None)`

    Downloads the assessment submission info into `directory` as a CSV file called `filename`.

    Parameter(s):
    - `filename`: The filename string. If not specified, it will be autogenerated in the form of `course_id.root_id.id.student_name.csv`
    - `directory`: The directory string. If not specified, it will save it to the corresponding course ID folder inside the `data` directory.

- `submission.submit()`

    Submits the submission. By right, this method should be useless since students are to submit on their own.

- `submission.compute_exp(total_grades, multiplier)`

    Math. Returns the EXP obtained from this submission.

    Parameter(s):
    - `total_grades`: The total grade as a number.
    - `multiplier`: The EXP multiplier as a number.

- `submission.grade(*grades, multiplier=1.0, publish=False)`

    Fills the grade of this submission and optionally publishes the grade.

    Parameter(s):
    - `*grades`: The grade for respective questions.
    - `multiplier`: The EXP multiplier as a number, set by default to `1.0`.
    - `publish`: A boolean whether to publish the grades, set by default to `False`.

- `submission.publish()`

    Publishes the submission, if unpublished. Note that if there's no existing grade, the submission gets published with 0 grades.

- `submission.mark()`

    Marks the submission, if unmarked. Note that if there's no existing grade, the submission gets marked with 0 grades.

- `submission.unsubmit()`

    Unsubmits the submission.

- `submission.set_exp(exp)`

    Manually sets the EXP obtained from this submission.

    Parameter(s):
    - `exp`: The EXP as a number.

- `submission.comment(question, text='')`

    Comments on the question ID obtained from `question` with the given `text`. See [`get_question_id`](#get_question_id) to see how the `question` variable is defined.

    Parameter(s):
    - `question`: A string or integer.
    - `text`: A HTML string. This should not be an empty string when the trailing and leading whitespaces are stripped.

- `submission.annotate(question, line, text='')`

    Annotates on the given line number `line` on the question ID obtained from `question` with the given `text`. See [`get_question_id`](#get_question_id) to see how the `question` variable is defined.

    Parameter(s):
    - `question`: A string or integer.
    - `line`: The line number as an integer.
    - `text`: A HTML string. This should not be an empty string when the trailing and leading whitespaces are stripped.

##### Example

```py
from coursemology_api import CourseAPI

course = CourseAPI(2352)

# Just the main assessments
# Use .df to convert to DataFrame
course.Assessments.flush_cache() # reset context cache
course.Assessments.info.df

# All assessments
course.Assessments.flush_cache() # reset context cache
with course.include_all_assessments():
    course.Assessments.info.df
    course.Assessments.info.to_csv('all_assessments.csv')

# Assessment questions
course.Assessments(54980).info.df
course.Assessments('Mission 0: Setting Up Python').info.df

# Duplicate first question of Mission 0 to Testing
# Since Testing is not a main assessments, need to provide context
with course.include_all_assessments():
    course.Assessments('Mission 0: Setting Up Python').duplicate('first', 'Testing')

# All submissions of a single assessment
course.Assessments(54980).Submissions.info.df
course.Assessments(54980).Submissions.info.meta

# Detailed submission statistics of a single assessment
course.Assessments(54980).Submissions.stats.df

# Info of a particular assessment submission
course.Assessments(54980).Submissions(1665572).info.df
course.Assessments(54980).Submissions('Russell Saerang').info.df
course.Assessments('Mission 0: Setting Up Python').Submissions('Russell Saerang').info.df

# Compute EXP with 16 marks and 20% penalty
course.Assessments(53062).Submissions(1666672).compute_exp(16, 0.8)

# Grade submission
# Assessment has three questions in this example
# 10% penalty applied
# Publish grade right away
course.Assessments(50060).Submissions(1559704).grade(10, 15, 15, multipler=0.9, publish=True)

# Manually set EXP to 0
course.Assessments(50060).Submissions(1559704).set_exp(0)

# Get question ID
course.Assessments(50060).Submissions(1559704).get_question_id('first')
course.Assessments(50060).Submissions(1559704).get_question_id(3) # third question
course.Assessments(50060).Submissions(1559704).get_question_id('last')

# Comment/annotate on submission
text = '<p><strong>This is wrong!</strong></p>
course.Assessments(50060).Submissions(1559704).comment('first', text)
course.Assessments(50060).Submissions(1559704).annotate('last', 14, text) # line 14
```

### [`Groups`](coursemology_api/groups.py)

[Back to top](#api)

##### Constructor

- `course.Groups`

    Represents the `Groups` instance attributed to the course.

- `course.Groups(group_id)`

    Represents a specific `Group` instance with the given `group_id`.

    Parameter(s):
    - `group_id`: The group ID as an integer.

- `course.Groups(group_name)`

    Represents a specific `Group` instance with the given `group_name`.

    Parameter(s):
    - `group_name`: The group name as a string.

##### Properties

- `groups.URL`

    The URL to the groups list.

- `groups.info`

    Returns a `Table` of the groups list. Each row contains:
    - the group ID
    - the group name
    - the list of group members
    - the list of group phantoms
    - the total number of members
    - the list of group managers
    - the group category ID
    - the group category name

- `group.info`

    Returns a `Table` of the group members list. Each row contains:
    - the user ID
    - the user name
    - the user role

##### Methods

- `groups.create(student_ids, tutor_ids, group_name, category_name, description=None)`

    Creates a group with the specified category and members/tutors. Returns the created `Group` object.

    Parameter(s):
    - `student_ids`: A list of student IDs as integers.
    - `tutor_ids`: A list of tutor IDs as integers.
    - `group_name`: The group name as a string.
    - `category_name`: The category name as a string. **There should be an existing category with this name.**
    - `description`: Optional group description as a string.

- `groups.create_category(category_name, description=None)`

    Creates a group category that contains multiple groups later on.

    Parameter(s):
    - `category_name`: The category name as a string. It is not enforced to have unique category names, thus allowing duplicate category names if one wishes to have such.
    - `description`: Optional group category description as a string.

- `groups.delete(category_id)`

    Deletes the specified group category.

    Parameter(s):
    - `category_id`: The ID of the group category as an integer.

- `group.update(student_ids, tutor_ids=[], group_name=None, description=None)`

    Updates the group with a fresh list of student IDs, tutor IDs, and optionally renaming the group name and description.

    Parameter(s):
    - `student_ids`: A list of student IDs as integers.
    - `tutor_ids`: A list of tutor IDs as integers.
    - `group_name`: Optional new group name as a string.
    - `description`: Optional new group description as a string.

- `group.delete()`

    Deletes the specified group.

##### Example

```py
from coursemology_api import CourseAPI

course = CourseAPI(2181)

# Get information about all groups
course.Groups.info.to_csv("groups.csv")
df_groups_all = course.Groups.info.df # work with table as dataframe

# Creating a group
group = course.Groups.create(
    student_ids=[62151,62153,62156], # sooyen, jon, kh
    tutor_ids=[62158,67354], # russell, wk
    group_name="Test Group",
    category_name="Default",
    description="This is a test group" # optional
)
print(group.info) # a Group instance, which supports .info as usual

# Get information about a particular group
## Using group name
group_name = "AFAST Russell"
course.Groups(name=group_name).info.to_csv(f"group_{group_name}.csv")
df_group = course.Groups(name=group_name).info.df # work with table as dataframe

## Using group ID
group_id = 3456
course.Groups(id=group_id).info.to_csv(f"group_{group_id}.csv")
df_group = course.Groups(id=group_id).info.df # work with table as dataframe
```

### [`LessonPlan`](coursemology_api/lesson_plan.py)

[Back to top](#api)

**NOTE: This is a feature in progress!**

##### Constructor

- `course.LessonPlan`

##### Properties

- `lesson_plan.URL`

- `lesson_plan.info`

##### Methods

- `lesson_plan.update(csvfilename)`

- `lesson_plan.update_item(item_path, item_data)`

##### Example

```py
from coursemology_api import CourseAPI

course = CourseAPI(2352)

# Use .df to work with DataFrames
course.LessonPlan.info.df
```

### [`Levels`](coursemology_api/levels.py)

[Back to top](#api)

##### Constructor

- `course.Levels`

    Represents the `Levels` instance of the course.

##### Properties

- `levels.URL`

    The URL to the levels list.

- `levels.info`

    Returns a `Table` of the level and the minimum EXP to reach the level. The metadata contains one information about whether one can manage the level thresholds.

##### Methods

- `levels.update(levels_dict)`

    Updates the level thresholds. The resulting level EXP threshold must be in increasing order when sorted by ascending level. There should not be any missing levels as well, e.g. level 8 after level 6.

    Parameter(s):
    - `levels_dict`: A dictionary of level-EXP pairs, both being integers.

##### Example

```py
from coursemology_api import CourseAPI
course = CourseAPI(2352)

# Use .df to work with DataFrames
course.Levels.info.df

# Updating level thresholds
course.Levels.update({47: 18300, 48: 19200, 49: 20200, 50: 21300})
```

### [`Surveys`](coursemology_api/surveys.py)

[Back to top](#api)

##### Constructor

- `course.Surveys`

    Represents the `Surveys` instance attributed to the course.

- `course.Surveys(survey_id)`

    Represents a specific `Survey` instance with the given `survey_id`.

    Parameter(s):
    - `survey_id`: The survey ID as an integer.

- `course.Surveys(survey_name)`

    Represents a specific `Survey` instance with the given `survey_name`.

    Parameter(s):
    - `survey_name`: The survey name as a string.

##### Properties

- `surveys.URL`

    The URL to the surveys page.

- `surveys.info`

    Returns a `Table` containing information about the surveys. Each row contains:
    - the survey ID
    - the survey name
    - the EXP obtained for doing the survey
    - the bonus EXP obtained for doing the survey before the bonus date
    - whether the survey is published or not
    - start time of the survey
    - end time of the survey
    - bonus end time of the survey
    - last time the closing reminder was sent
    - whether the survey is anonymous or not

- `survey.URL_RESULTS`

    The URL to the JSON format of the survey results.

- `survey.URL_RESPONSES`

    The URL to the JSON format of the survey responses.

- `survey.info`

    Returns a `Table` containing information about a specific survey. It is optional to exclude phantoms within the table.

    When the survey is anonymous, the fall-back method to obtain the table is to export the responses via downloading them.

    Each row contains:
    - the student ID
    - the student name
    - whether the student is a phantom or not
    - submission status: either `'not started'`, `'responding'`, `'submitted'`
    - time of survey submission, if submitted
    - the question responses, _one question per column_

    The metadata contains:
    - the survey ID
    - the survey name
    - the base EXP for doing the survey
    - the bonus EXP for doing the survey before the bonus end time
    - whether the survey is published or not
    - start time of the survey
    - end time of the survey
    - whether the survey allows responses after it ends
    - whether the survey allows modification after submission
    - the survey description
    - whether the survey can be updated
    - whether the survey can be deleted
    - whether sections can be created within the survey
    - whether survey results can be viewed
    - whether students can respond to the survey
    - whether the survey has a student response
    - whether the survey is anonymous

##### Methods

N/A.

##### Example

```py
from coursemology_api import CourseAPI

course = CourseAPI(2352)

# Work with .df for DataFrames
course.Surveys.info.df

# Specific survey with given ID
course.Surveys(1424).info.df
course.Surveys(1424).info.meta

# Specific survey with given name
course.Surveys('Offline PE Survey').info.df
```

### [`Users`](coursemology_api/users.py)

[Back to top](#api)

##### Constructor

- `course.Users`

    Represents the `Users` instance attributed to the course.

- `course.Users(user_id)`

    Represents a specific `User` instance with the given `user_id`.

    Parameter(s):
    - `user_id`: The user ID as an integer.

- `course.Users(user_name)`

    Represents a specific `User` instance with the given `user_name`.

    Parameter(s):
    - `user_name`: The user name as a string.

- `course.Users.Students`

    Represents the `Students` instance attributed to the course.

- `course.Users.Students(student_id)`

    Represents a specific `User` instance with the given `student_id`. The difference between this and `course.Users(user_id)` is the enforcement on the user being a student.

    Parameter(s):
    - `student_id`: The student ID as an integer.

- `course.Users.Students(student_name)`

    Represents a specific `User` instance with the given `student_name`. The difference between this and `course.Users(student_name)` is the enforcement on the user being a student.

    Parameter(s):
    - `student_name`: The student name as a string.

- `course.Users.Staff`

    Represents the `Staff` instance attributed to the course.

- `course.Users.Staff(staff_id)`

    Represents a specific `User` instance with the given `staff_id`. The difference between this and `course.Users(user_id)` is the enforcement on the user being a staff.

    Parameter(s):
    - `staff_id`: The staff ID as an integer.

- `course.Users.Staff(staff_name)`

    Represents a specific `User` instance with the given `staff_name`. The difference between this and `course.Users(staff_name)` is the enforcement on the user being a staff.

    Parameter(s):
    - `staff_name`: The staff name as a string.

- `course.Users(user_id_or_user_name).ExpRecords`

    Represents an `ExpRecords` instance attributed to the user with the given `user_id` or `user_name`.

    Parameter(s):
    - Either one of the following:
        - `user_id`: The user ID as an integer.
        - `user_name`: The user name as a string.

- `course.Users(user_id_or_user_name).PersonalTimes`

    Represents a `PersonalTimes` instance attributed to the user with the given `user_id` or `user_name`.

    Parameter(s):
    - Either one of the following:
        - `user_id`: The user ID as an integer.
        - `user_name`: The user name as a string.

##### Properties

- `users.URL`

    The URL to the users list.

- `users.info`

    Returns a `Table` of the users list where each row contains:
    - the user ID
    - the user name
    - the user email
    - the timeline algorithm attributed to the user
    - the role of the user
    - whether the user is a phantom or not

- `students.URL`

    The URL to the students list.

- `students.URL_STATS`

    The URL to the statistics of all students.

- `students.info`

    Same as `users.info` but only for students.

- `students.stats`

    Returns a `Table` of the students statistics where each row contains:
    - the student ID
    - the student name
    - the student's tutor(s)
    - the student's current level
    - the student's current EXP
    - the number of videos watched
    - the proportion of the videos watched
    - whether the student is a phantom or not
    - EXP obtained from the main assessments (missions and side quests), one column per each of them

- `staff.URL`

    The URL to the staff list.

- `staff.URL_STATS`

    The URL to the statistics of all staff.

- `staff.info`

    Same as `users.info` but only for staff.

- `staff.stats`

    Returns a `Table` of the staff statistics where each row contains:
    - the staff ID
    - the staff name
    - the number of submissions marked
    - the number of students under the staff
    - the average time needed to grade per assignment
    - standard deviation of the time needed to grade

- `exp_records.URL`

    The URL to the EXP records of a specific user.

- `exp_records.info`

    Returns a `Table` of the EXP records of a specific user where each row contains:
    - the record ID
    - the reason of EXP record
    - the submission URL
    - the EXP awarded on the record
    - the user ID of the record updater
    - the user name of the record updater
    - the time of the record update

- `personal_times.URL`

    The URL to the personal times of a specific user.

- `personal_times.info`

    Returns a `Table` of the personal times of a specific user where each row contains:
    - the reference timing ID
    - the personal time ID
    - the personal time type
    - the personal time title
    - the reference start time
    - the reference bonus end time
    - the reference end time
    - the personal time's start time
    - the personal time's bonus end time
    - the personal time's end time

##### Methods

- `users.exp_disburse(reason_for_disbursement, student_id_exp_pairs=[])`

    Disburses EXP to multiple students with a common reason. Usually used by forum ICs and tutorial ICs.

    Parameter(s):
    - `reason_for_disbursement`: The reason for disbursement as a string.
    - `student_id_exp_pairs`: A list of **integer pairs** in the form of `(user_id, exp)`.

- `users.invite(data)`

    To be implemented.

- `user.update(name=None, timeline_algorithm=None, phantom=None)`

    Updates the user settings. It is optional to provide each parameter.

    Parameter(s):
    - `name`: The new name as a string.
    - `timeline_algorithm`: This determines the personal timeline algorithm of the user. The value is one of these four strings:
        - `'fixed'`: Start time and end time don't change.
        - `'fomo'`: Start time may shift earlier but end time remains.
        - `'stragglers'`: End time may shift later but start time remains.
        - `'otot'`: Start time may shift earlier and end time may shift later.
    - `phantom`: Either `0` or `1`, specifying whether this user is a phantom or not.

- `user.delete()`

    Deletes the user.

- `exp_record.update(reason='', exp=None)`

    Updates a particular EXP record of an user. It is optional to provide `reason` but `exp` is required.

    Parameter(s):
    - `reason`: The new record reason as a string.
    - `exp`: The new EXP of this record as an integer.

- `exp_record.delete()`

    Deletes this EXP record.

- `personal_times.recompute()`

    Recomputes the personal time.

##### Example

```py
from coursemology_api import CourseAPI

course = CourseAPI(2352)

# Work with .df for handling DataFrames
course.Users.info.df
course.Users.Students.info.df
course.Users.Staff.info.df

# Getting student statistics
course.Users.Students.stats.to_csv('students_stats.csv')
course.Users.Students.flush_cache() # .stats is cached, so we flush it first
with course.include_phantoms():
    course.Users.Students.stats.to_csv('students_stats_including_phantom.csv')
df_student_stats = course.Users.Students.stats.df # work with table as dataframe

# Disburse EXP!
# ID 61234 gets 500 EXP, ID 62345 gets 600 EXP, ID 63456 gets 700 XP
exp_pairs = [(61234, 500), [62345, 600], {0: 63456, 1: 700}]
course.Users.exp_disburse('Forum EXP for Week 14', exp_pairs)

# Getting a specific student
course.Users.Students(67890)
course.Users.Students('John Doe')

# Getting a specific staff
course.Users.Staff(67891)
course.Users.Staff('Jane Doe')

# Update student particulars
# Student name becomes 'New Name', timeline algorithm is OTOT
# Phantom yes/no status remains
course.Users.Students(67890).update(name='New Name', timeline_algorithm='otot')

# EXP records
course.Users.Students(67890).ExpRecords.info.df
course.Users.Students(67890).ExpRecords(123456).update('Wrong record', 0)
    # update record to 0 EXP since it's a misdisbursement, let's say

# Personal times
course.Users.Students(67890).PersonalTimes.info.df
course.Users.Students(67890).PersonalTimes.recompute()
```

### [Utility](coursemology_api/utility.py)

The following classes and functions act as helper or utility for other main Coursemology classes and their functionalities.

#### `WithContext`

[Back to top](#api)

This class serves as an instance that provides some context. To use it on a course, use it along with the `with` statement. For example, the code below.

```py
from coursemology_api import CourseAPI

course = CourseAPI(2352)

with course.include_phantoms():
    # code here...
```

#### `Table`

[Back to top](#api)

A wrapper class for tables and dataframe-like objects. Contains `headers` for the header list, `data` for the data itself, and optionally `metadata` as a dictionary.

The `Table` class supports conversion to Pandas DataFrame using the `df` property and CSV files using the `to_csv(filename)` method.

For example:

```py
headers = ['A', 'B', 'C']
data = [[3*i + j for j in range(3)] for i in range(3)]

# A  B  C
# 0  1  2
# 3  4  5
# 6  7  8
Table(headers=headers, data=data)

# Pandas DataFrame
Table(headers=headers, data=data).df

# Convert to CSV file named table.csv
Table(headers=headers, data=data).to_csv('table.csv')
```

#### `Rooted`

[Back to top](#api)

Helper class to create the overall class hierarchy, since some classes are functionally dependant on the existence of another class. For example, `Users` that represents the user list and `User` that represents a single user.

#### `HTTP`

[Back to top](#api)

Wrapper class for several web-related functionalities.

- HTTP requests: `GET`, `POST`, `PATCH`, `DELETE`
- Managing cookies: loading and dumping cookies

For example:

```py
from coursemology_api import CourseAPI

course = CourseAPI(2352)

# Sample GET request
course.HTTP.get('https://www.example.com')
```

#### `ISODatetime`

[Back to top](#api)

Wrapper class for datetime objects. Constructed with an ISO-format string.

For example:

```py
from datetime import timedelta
dt = ISODatetime('2022-12-19T10:30:00.000+08:00') # 19 December 2022, 10:30 AM GMT+8

dt.date() # datetime.date(2022, 12, 19)
dt.time() # datetime.time(10, 30)
dt + timedelta(days=12) # 2022-12-31T02:30:00.000Z
```

#### `redirect`

A wrapper function to check for redirection of every HTTP request to the sign in page. It will make use of the cached `.coursemology/login.pkl` file if possible and requests for login particulars as usual otherwise.

Sometimes, the request might not be fully processed and thus a status code of 202 is shown. In this case, we delay the re-request for 2 seconds.

#### `guess_id`

A utility function to help getting the Coursemology ID of a particular instance. It can be a student ID, assessment ID, etc. If the `id` parameter is passed, it will check if the parameter is already a valid ID.

On some scenarios, the `name` parameter is used instead since some users find it easier to access by name over by ID. In this case, it will try to find the ID of the instance associated with `name`.

Suppose both methods fail, this function will try to look at the higher level instances where the information is entailed. For example, when the searching on `Assessment` fails, it will try to look at `Assessments`.

In the worst case, this function throws an exception for being unable to find a suitable ID.

#### `get_question_id`

Similar to `guess_id` but for questions. The following cases are checked in order, based on the value of `question`.
- If equal to `'first'`, it will take the ID of the first question.
- If equal to `'last'`, it will take the ID of the last question.
- If already an existing ID itself, it will take itself.
- If an integer/string $n$, take the $n$-th question ID. Note that this uses 1-based indexing.
- Use itself as the question ID otherwise.

Sample usage of this function: `submission.comment` and `submission.annotate`


## Acknowledgement

Codebase forked from `cs1010s/cs1010sx_auto`.