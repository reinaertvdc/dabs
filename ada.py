from os import listdir
from os.path import join

from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC

from browser import Browser


class Ada:
    def __init__(self, settings: object):
        self._browser = Browser()
        b = self._browser

        self._session_cookie_file_path = 'ada_session_cookie'
        self._session_cookie_name = 'ASP.NET_SessionId'

        s = settings

        # URL to the certificate search page.
        self._search_url = '%s://%s:%s@%s/%s?%s' % (
            s.scheme, s.username, s.password, s.host, s.path, s.query_string)

        # Ada may not work when a previous session is still active. If it
        # works, store the new session cookie for future use. If not, look for
        # an existing session cookie, load it, and try again.
        if self._is_working():
            self._store_session_cookie()
        else:
            try:
                self._load_session_cookie()
            except:
                raise Exception('Could not open Ada in a new session, ' +
                                'and no old session cookie was found')

            if not self._is_working():
                raise Exception('Could not open Ada in a new session, ' +
                                'and the old session cookie does not work')

    def download_cert_image(self, category: str, year: str, names: str='',
                            number: str='') -> str:
        b = self._browser

        # Open the search page.
        b.get(self._search_url)
        b.find_element_by_id('ctl00_Plh1_lnkButtons_pnlButtons').find_elements_by_tag_name('a')[3].click()

        # Enter the search criteria.
        id_prefix = "//*[@name='ctl00_Plh1_grd_"
        b.find_element_by_xpath(
            id_prefix + "fltcat']").send_keys(category)
        b.find_element_by_xpath(id_prefix + "flttitle']").send_keys(names)
        if year:
            b.find_element_by_xpath(id_prefix + "flttitle']").send_keys(' ' + year)
        if number:
            b.find_element_by_xpath(id_prefix + "flttitle']").send_keys(' ' + number)

        # Submit the search.
        b.find_element_by_xpath(id_prefix + "flttitle']").send_keys(Keys.ENTER)

        # Open the list of matches.
        table = b.find_element_by_id(
            'ctl00_Plh1_grd_documentlist').find_element_by_tag_name('tbody')
        certs = table.find_elements_by_class_name('ListContent')

        # Abort if not exactly one match is found, since we need exactly one
        # match to be sure of which file to download.
        if len(certs[0].find_elements_by_tag_name('td')) == 1:
            raise Exception('Found no matches')
        if len(certs) > 1:
            raise Exception('Found multiple matches')

        # It's dangerous to assume the name of the downloaded file, so we make
        # sure the download directory is empty before downloading, making the
        # downloaded file only one in it, so as to avoid confusion.
        b.empty_download_dir()

        # Click the download button.
        b.find_element_by_css_selector(
            'img[src="./Images/FileTypes/tif.gif"]').click()

        # Wait until the certificate is downloaded.
        b.wait_until(lambda _: len(listdir(b.download_dir)) == 1)

        # Each certificate download opens a popup window, so make sure all
        # popup windows are closed again.
        b.close_all_popup_windows()

        # Return the path to the downloaded certificate.
        return join(b.download_dir, listdir(b.download_dir)[0])

    def quit(self) -> None:
        self._browser.quit()

    def _is_working(self) -> bool:
        try:
            self._browser.get(self._search_url)
            self._browser.verify(
                EC.presence_of_element_located((By.CLASS_NAME, 'DetailTable')))

            return True
        except Exception:
            return False

    def _load_session_cookie(self) -> None:
        with open(self._session_cookie_file_path) as f:
            cookie_string = f.read()

        self._browser.add_cookie(eval(cookie_string))

    def _store_session_cookie(self) -> None:
        with open(self._session_cookie_file_path, 'w') as f:
            f.write(str(self._browser.get_cookie(self._session_cookie_name)))
