import os
from os import makedirs
from os.path import dirname, exists, join, realpath
from shutil import rmtree
from typing import Any, Callable, Optional

from selenium.webdriver import Chrome, ChromeOptions
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support.ui import WebDriverWait


class Browser(Chrome):
    DEFAULT_WAIT_TIME = 30

    def __init__(self):
        self._download_dir = join(dirname(realpath(__file__)), 'download')
        self._wait_time = self.DEFAULT_WAIT_TIME
        print(self._wait_time)

        options = ChromeOptions()
        options.add_experimental_option('prefs', {
            'download.default_directory': self._download_dir
        })

        executable_name = None

        if (os.name == 'posix'):
            executable_name = 'chromedriver_linux64'
        elif (os.name == 'nt'):
            executable_name = 'chromedriver_windows32.exe'
        elif (os.name == 'mac'):
            executable_name = 'chromedriver_mac'
        else:
            raise Exception("Unsupported OS '%s'" % os.name)

        super().__init__(join('webdriver', executable_name),
                         chrome_options=options)

        self.implicitly_wait(self._wait_time)
        self.maximize_window()

    @property
    def download_dir(self):
        return self._download_dir

    @property
    def wait_time(self):
        return self._wait_time

    def double_click(self, element: WebElement) -> None:
        ActionChains(self).double_click(element).perform()

    def find_element_by_text(self, text: str,
                             parent: Optional[WebElement]=None) -> WebElement:
        if parent is None:
            parent = self

        return parent.find_element_by_xpath(
            "//*[contains(text(), '%s')]" % (text))

    def scroll_up(self) -> None:
        self.execute_script('window.scrollTo(0, 0);')

    def scroll_down(self) -> None:
        self.execute_script('window.scrollTo(0, document.body.scrollHeight);')

    def empty_download_dir(self) -> None:
        if exists(self.download_dir):
            rmtree(self.download_dir)

        makedirs(self.download_dir)

    def close_all_popup_windows(self) -> None:
        current_window_handle = self.current_window_handle

        for window_handle in self.window_handles:
            if window_handle != current_window_handle:
                self.switch_to.window(window_handle)
                self.close()

        self.switch_to.window(current_window_handle)

    def wait_until(self, condition: Callable[[], Any],
                   wait_time: Optional[int]=None,
                   parent: Optional[WebElement]=None) -> None:
        self._wait(lambda w: w.until(condition), wait_time, parent)

    def wait_until_not(self, condition: Callable[[], Any],
                       wait_time: Optional[int]=None,
                       parent: Optional[WebElement]=None) -> None:
        self._wait(lambda w: w.until_not(condition), wait_time, parent)

    def verify(self, condition: Callable[[], Any],
               parent: Optional[WebElement]=None) -> None:
        self.wait_until(condition, 0, parent)

    def verify_not(self, condition: Callable[[], Any],
                   parent: Optional[WebElement]=None) -> None:
        self.wait_until_not(condition, 0, parent)

    def _wait(self, condition: Callable[[WebDriverWait], Any],
              wait_time: Optional[int]=None,
              parent: Optional[WebElement]=None) -> None:
        if wait_time is None:
            wait_time = self.wait_time

        if parent is None:
            parent = self

        self.implicitly_wait(wait_time)
        condition(WebDriverWait(parent, wait_time))
        self.implicitly_wait(self._wait_time)
