from __future__ import annotations
from typing import Iterable
import webbrowser
import logging


LOGGER = logging.getLogger(__name__)


def open_urls(auth_urls: Iterable[str]) -> None:
    to_be_opened_in_browser = list(filter(lambda auth_url: auth_url != "", auth_urls))
    if len(to_be_opened_in_browser) > 0:
        LOGGER.info("opening urls in browser " + str(to_be_opened_in_browser))
        for url in to_be_opened_in_browser:
            webbrowser.open(url)
    else:
        LOGGER.info(f"no urls found to be opened {to_be_opened_in_browser}")
