from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time

# Налаштування Chrome з режимом інкогніто
options = webdriver.ChromeOptions()
options.add_argument("--incognito")
driver = webdriver.Chrome(
    service=Service(ChromeDriverManager().install()),
    options=options
)
driver.get("http://127.0.0.1:8000/login/")

# Очікування відображення reCAPTCHA
captcha_container = WebDriverWait(driver, 15).until(
    EC.presence_of_element_located((By.CLASS_NAME, "g-recaptcha"))
)

# Знаходимо iframe reCAPTCHA
iframe = driver.find_element(By.XPATH, "//iframe[@title='reCAPTCHA']")
driver.switch_to.frame(iframe)

checkbox = WebDriverWait(driver, 15).until(
    EC.element_to_be_clickable((By.ID, "recaptcha-anchor"))
)
checkbox.click()

driver.switch_to.default_content()

time.sleep(5)

submit_button = driver.find_element(By.CLASS_NAME, "btn-primary")
submit_button.click()

time.sleep(35)

driver.quit()