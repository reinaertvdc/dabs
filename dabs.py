from itertools import combinations
from os import rename, system
from os.path import splitext, exists
from time import sleep

from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC

from ada import Ada
from browser import Browser


class Dabs:
    def __init__(self, ada: Ada, settings: object):
        self._browser = Browser()
        self._ada = ada
        self._skip_counter_file_path = 'dabs_skip_counter'
        self._skip_counter = 0
        self._max_year = 2017

        s = settings

        # URL to the list of certificates to be validated.
        self._certs_list_url = '%s://%s/%s?%s' % (
            s.scheme, s.host, s.path, s.query_string)

        self._username = s.username
        self._password = s.password

        self._load_skip_counter()

    def validate_all_certs(self) -> None:
        self._init()

        self._browser.execute_script('document.body.style.zoom = "100%";')

        while self._validate_cert(self._skip_counter):
            pass

    def quit(self) -> None:
        self._ada.quit()
        self._browser.quit()

    def _load_skip_counter(self) -> None:
        if exists(self._skip_counter_file_path):
            with open(self._skip_counter_file_path) as f:
                self._skip_counter = int(f.read())
        else:
            self._store_skip_counter()

    def _store_skip_counter(self) -> None:
        with open(self._skip_counter_file_path, 'w') as f:
            f.write(str(self._skip_counter))

    def _skip(self) -> None:
        self._skip_counter += 1
        self._store_skip_counter()

    def _init(self) -> None:
        # Attempt to open the list of certificates to be validated. A login
        # prompt will open, which will redirect us to the requested page once
        # valid credentials are entered.
        self._browser.get(self._certs_list_url)

        # Log in.
        form = self._browser.find_element_by_id('kc-form-login')
        form.find_element_by_name('username').send_keys(self._username)
        form.find_element_by_name('password').send_keys(self._password)
        sleep(0.5)
        form.find_element_by_name('login').click()
        sleep(1)

    def _wait_until_cert_list_is_loaded(self) -> None:
        sleep(0.3)

    def _sort_certs_asc_by_date(self) -> None:
        def get_toggle_button(): return self._browser.find_element_by_xpath(
            "//th[@psortablecolumn='factDate.year']")

        toggle_button = get_toggle_button()

        try:
            self._browser.verify(EC.presence_of_element_located(
                (By.CLASS_NAME, 'fa-sort-asc')), toggle_button)
        except Exception:
            toggle_button.click()

        self._wait_until_cert_list_is_loaded()

    def _validate_cert(self, index: int) -> None:
        b = self._browser

        for _ in range(10):
            try:
                self._browser.find_element_by_class_name('ui-table-loading')
                self._browser.refresh()
                sleep(2)
            except Exception:
                break

        certs_per_page = 10
        desired_page_index = int(index / certs_per_page) + 1
        index_within_page = index % certs_per_page

        self._open_certs_page(desired_page_index)

        self._wait_until_cert_list_is_loaded()

        table = b.find_element_by_tag_name('tbody')
        certs = table.find_elements_by_tag_name('tr')
        cert = certs[index_within_page]
        cells = cert.find_elements_by_tag_name('td')

        category = cells[1].text
        number = cells[3].text
        year = cells[4].text[-4:]
        names = []

        if int(year) > self._max_year:
            return False

        for name in cells[5].text.split(','):
            names.append(name.split()[-1])

        names.extend(combinations(names, 2))
        names = reversed(names)

        if int(number) > 0:
            number = number.rjust(4, '0')
        else:
            number = None

        if category == 'Huwelijk':
            category = 'Huwelijksakte'
        elif category == 'Overlijden':
            category = 'Overlijdensakte'
        elif category == 'Geboorte':
            category = 'Geboorteakte'
        else:
            self._skip()

            return True

        image_path = None
        err = None

        try:
            if number is not None:
                image_path = self._ada.download_cert_image(
                    category, year, None, number)
        except Exception as e:
            err = e

        if image_path is None:
            for name in names:
                name = ' '.join(name) if isinstance(name, tuple) else name

                try:
                    image_path = self._ada.download_cert_image(
                        category, year, name, None)
                except Exception as e:
                    err = e

                try:
                    if image_path is None and number is not None:
                        image_path = self._ada.download_cert_image(
                            category, year, name, number)
                except Exception as e:
                    err = e

                if image_path is not None:
                    break

        if image_path is None:
            self._skip()

            return True

        basename, extension = splitext(image_path)

        if extension == '.tif':
            new_image_path = basename + '.tiff'
            rename(image_path, new_image_path)
            image_path = new_image_path
        else:
            self._skip()

            return True

        success = False

        b.double_click(cert)

        for _ in range(5):
            try:
                sleep(1)
                b.find_element_by_class_name('ui-fileupload')
                success = True
                break
            except Exception:
                b.refresh()

        if not success:
            self._skip()

            return True

        file_input = None

        for _ in range(10):
            try:
                file_input = b.find_element_by_class_name(
                    'ui-fileupload-choose').find_element_by_tag_name('input')

                file_input.send_keys(new_image_path)

                sleep(1)

                b.find_element_by_class_name('ui-icon-delete')

                break
            except Exception:
                b.refresh()
                sleep(2)

        buttons = b.find_elements_by_class_name('ui-button-text-only')

        if buttons[2].is_enabled():
            buttons[2].click()
        else:
            buttons[1].click()

            self._skip()
        
        sleep(0.3)

        return True

    def _open_certs_page(self, index: int) -> None:
        b = self._browser

        current_page = None

        self._sort_certs_asc_by_date()

        while True:
            paginator = b.find_element_by_class_name('ui-paginator-pages')
            current_page = int(paginator.find_element_by_class_name(
                'ui-state-active').text)

            if current_page == index:
                break

            page_buttons = paginator.find_elements_by_tag_name('a')

            clicked = False

            for page_button in page_buttons:
                if index <= int(page_button.text):
                    page_button.click()

                    clicked = True

                    sleep(0.5)

                    break

            if not clicked:
                page_buttons[-1].click()
                sleep(0.5)
