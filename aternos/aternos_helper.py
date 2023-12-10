import time
from os import path

import undetected_chromedriver as uc

from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from webdriver_manager.chrome import ChromeDriverManager

class Aternos:

    def __init__(self, username: str, password: str):
        self.username = username
        self.password = password

        self.status = "offline"

        self.busy = False

        self.driver = uc.Chrome(driver_executable_path=ChromeDriverManager().install(), headless=False, use_subprocess=False)


    def check_logged_on(self):
        self.driver.get("https://aternos.org/servers/")

        self.driver.implicitly_wait(5)

        if self.driver.current_url.startswith("https://aternos.org/go"):
            self.login()

    def login(self):
        username = self.driver.find_element(By.CLASS_NAME, "username")
        username.send_keys(self.username)

        password = self.driver.find_element(By.CLASS_NAME, "password")
        password.send_keys(self.password)

        login_button = self.driver.find_element(By.CLASS_NAME, "login-button")
        login_button.click()

        self.driver.implicitly_wait(5)


    def start_server(self):
        self.busy = True

        self.check_logged_on()

        status = self.driver.find_element(By.CLASS_NAME, "servercard")

        self.status = "offline"
        if "offline" in status.get_attribute("class"):
            status.click()
            self.driver.implicitly_wait(5)

            WebDriverWait(self.driver, 10).until(EC.element_to_be_clickable((By.ID, "start")))
            start = self.driver.find_element(By.ID, "start")

            try:
                start.click()
            except:
                accept = self.driver.find_element(By.CSS_SELECTOR, "[mode=primary]")
                accept.click()
                self.driver.refresh()
                WebDriverWait(self.driver, 10).until(EC.element_to_be_clickable((By.ID, "start")))
                start = self.driver.find_element(By.ID, "start")
                start.click()

            WebDriverWait(self.driver, 10).until(EC.element_to_be_clickable((By.CSS_SELECTOR, "#theme-switch > dialog > main > div.alert-buttons.btn-group > button")))
            start = self.driver.find_element(By.CSS_SELECTOR, "#theme-switch > dialog > main > div.alert-buttons.btn-group > button")
            start.click()

            self.status = "starting"

            while self.status != "started":
                time.sleep(10)
                self.driver.refresh()

                status = self.driver.find_element(By.CLASS_NAME, "navigation-server")
                if "online" in status.get_attribute("class"):
                    self.status = "started"

        elif "loading" in status.get_attribute("class"):
            self.status = "starting"
        elif "online" in status.get_attribute("class"):
            self.status = "started"

        self.busy = False


if __name__ == "__main__":
    aternos = Aternos("wyborowa2", "221298")

    aternos.start_server()

    print(aternos.status)