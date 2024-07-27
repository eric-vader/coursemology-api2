from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
import json

def authenticate(username, password, wait_time=10, headless=True):
    URL = 'https://coursemology.org/user/profile/edit'
    options = Options()
    if headless:
        options.add_argument('--headless=new')
    driver = webdriver.Chrome(options=options)
    driver.get(URL)
    username_field = WebDriverWait(driver, wait_time).until(EC.presence_of_element_located((By.CSS_SELECTOR, 'input[name="email"]')))
    password_field = driver.find_element(By.CSS_SELECTOR, 'input[name="password"]')
    submit_button = driver.find_element(By.CSS_SELECTOR, 'button[type="submit"]')
    remember_checkbox = driver.find_element(By.CSS_SELECTOR, 'input[name="rememberMe"]')
    username_field.send_keys(username)
    password_field.send_keys(password)
    remember_checkbox.click()
    submit_button.click()
    driver.get(URL) # visit an authenticatable page, otherwise cookies are not set
    WebDriverWait(driver, wait_time).until(EC.presence_of_element_located((By.CSS_SELECTOR, '.MuiAvatar-root')))
    localstorage = driver.execute_script("return localStorage;")
    key = [k for k in localstorage.keys() if 'auth.coursemology' in k][0]
    auth_data = json.loads(localstorage[key])
    id_token = auth_data['id_token']
    return id_token, driver.get_cookies()
