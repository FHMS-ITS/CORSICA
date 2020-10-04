import logging
import uuid
from time import sleep

import docker
from selenium import webdriver
from selenium.common.exceptions import JavascriptException
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.common.by import By

from utils.docker import pull_image, get_images_tags
from utils.log import _error, _info
from utils.utils import convert_path_to_absolute_if_relative


class SeleniumTester():
    def __init__(self, script_path, data_path):
        self.script_path = convert_path_to_absolute_if_relative(script_path)
        self.data_path = convert_path_to_absolute_if_relative(data_path)
        self.docker_client = docker.from_env()
        self.container = {}
        self.docker_images = get_images_tags("selenium/*")

    def start_container(self, browser):
        if 'selenium/standalone-{}'.format(browser) not in self.docker_images:
            pull_image('selenium/standalone-{}'.format(browser))

        uid = str(uuid.uuid1()).split("-")[0]
        volumes = {self.script_path: {'bind': '/srv/scripts', 'mode': 'ro'},
                   self.data_path: {'bind': "/srv/data", 'mode': "ro"}}

        self.container[browser] = self.docker_client.containers.create(
            image="selenium/standalone-{}:latest".format(browser),
            name="selenium_{}".format(uid),
            volumes=volumes,
            network='corsica-network',
        )
        self.container[browser].start()

    def stop_container(self, browser):
        self.container[browser].kill()
        self.container[browser].remove()

    def execute(self, browser, timeout=1160, file='index.html', show_errors=False):
        capabilities = None
        if browser == "chrome":
            capabilities = DesiredCapabilities.CHROME
        elif browser == "firefox":
            capabilities = DesiredCapabilities.FIREFOX
        elif browser == "opera":
            capabilities = DesiredCapabilities.OPERA
        container = self.container[browser].name if self.container[browser] else 'localhost'
        driver = None
        logging.getLogger('urllib3.util.retry').setLevel('ERROR')
        try:
            # Wait for Selenium to start
            while True:
                try:
                    driver = webdriver.Remote(command_executor='http://{}:4444/wd/hub'.format(container),
                                              desired_capabilities=capabilities)
                    break
                except:
                    sleep(1)

            driver.set_page_load_timeout(timeout)
            driver.get('file:///srv/scripts/{}'.format(file))
            WebDriverWait(driver, timeout).until(expected_conditions.presence_of_element_located((By.ID, 'result')))
            result = driver.find_element_by_id('result').text
            if show_errors:
                for entry in driver.get_log('browser'):
                    _error('selenium', entry)
        except Exception as e:
            result = "{}"

            _error("selemium", "Result Empty: {} {}".format(type(e).__name__, e))
            _error("selemium", "Datapath: {}".format(self.data_path))
            for entry in driver.get_log('browser'):
                _error('selenium', entry)

        finally:
            if driver:
                driver.close()

        return result

    def run(self, browser, timeout=11600, file='index.html', show_errors=False):
        try:
            self.start_container(browser)
            result = self.execute(browser, timeout, file, show_errors)
        finally:
            self.stop_container(browser)
        return result
