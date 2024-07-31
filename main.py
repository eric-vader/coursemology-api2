from coursemology_api import CourseAPI
course = CourseAPI(2851)
course.login()

course.Assessments.flush_cache() # reset context cache
with course.include_all_assessments():
    print(course.Assessments.info.df)

# from selenium import webdriver
# browser = webdriver.Firefox()
# browser.get('http://selenium.dev/')