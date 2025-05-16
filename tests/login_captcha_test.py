from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time

# Налаштування Selenium
driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))
driver.get("http://127.0.0.1:8000/login/")

# Перевірка відображення reCAPTCHA
captcha_container = WebDriverWait(driver, 15).until(
    EC.presence_of_element_located((By.CLASS_NAME, "g-recaptcha"))
)
assert captcha_container.is_displayed()

# Знаходимо iframe reCAPTCHA
iframe = driver.find_element(By.XPATH, "//iframe[@title='reCAPTCHA']")
driver.switch_to.frame(iframe)

# Намагаємося натиснути на чекбокс reCAPTCHA
checkbox = WebDriverWait(driver, 15).until(
    EC.element_to_be_clickable((By.ID, "recaptcha-anchor"))
)
checkbox.click()

# Повертаємося до основного контенту
driver.switch_to.default_content()

# Чекаємо, щоб перевірити поведінку
time.sleep(5)

# Спроба відправити форму без повного вирішення CAPTCHA
submit_button = driver.find_element(By.CLASS_NAME, "btn-primary")
submit_button.click()

# Чекаємо на реакцію (збільшений час)
time.sleep(10)

# Перевірка, чи залишились на сторінці входу
current_url = driver.current_url
assert "login" in current_url.lower()

# Перевірка помилки в messages або errorlist
messages = driver.find_elements(By.CLASS_NAME, "messages")
errorlist = driver.find_elements(By.CLASS_NAME, "errorlist")
has_captcha_error = False

for msg in messages:
    if "captcha" in msg.text.lower():
        has_captcha_error = True
        break

if not has_captcha_error:
    for err in errorlist:
        if "captcha" in err.text.lower():
            has_captcha_error = True
            break

assert has_captcha_error

driver.quit()