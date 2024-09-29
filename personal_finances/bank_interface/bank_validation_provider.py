from __future__ import annotations
from typing import Type, Optional
from types import TracebackType
import subprocess
import os
import signal
import logging
import requests
from abc import ABC, abstractmethod

LOGGER = logging.getLogger(__name__)


class BankValidationProvider(ABC):
    @abstractmethod
    def is_reference_validated(self, reference_id: str) -> bool:
        pass

    @abstractmethod
    def get_validation_url(self, reference_id: str) -> str:
        pass


class LocalhostValidationProvider(BankValidationProvider):
    def __enter__(self) -> LocalhostValidationProvider:
        self._web_authorizer_process = subprocess.Popen(
            [
                "uvicorn",
                "personal_finances.bank_interface.bank_localhost_validator:app",
                "--reload",
            ],
            preexec_fn=os.setpgrp,
        )
        LOGGER.info("uvicorn server started")
        return self

    def __exit__(
        self,
        exc_type: Optional[Type[BaseException]],
        exc_value: Optional[BaseException],
        traceback: Optional[TracebackType],
    ) -> None:
        os.killpg(
            os.getpgid(self._web_authorizer_process.pid),
            signal.SIGTERM,
        )
        LOGGER.info("uvicorn server killed")

    def is_reference_validated(self, reference_id: str) -> bool:
        validations = requests.get(
            "http://127.0.0.1:8000/validations/", verify=False
        ).json()
        return reference_id in validations

    def get_validation_url(self, reference_id: str) -> str:
        return f"https://127.0.0.1/validations/{reference_id}"
