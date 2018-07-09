#!/usr/bin/env python3

from datetime import datetime

from ada import Ada
from browser import Browser
from dabs import Dabs
import settings

Browser.DEFAULT_WAIT_TIME = settings.wait_time

for i in range(600):
    ada = Ada(settings.ada)
    dabs = Dabs(ada, settings.dabs)

    try:
        dabs.validate_all_certs()
        dabs.quit()

        break
    except Exception as e:
        print('Run %d at %s:' % (i, datetime.now()))
        print(e)

        dabs.quit()
