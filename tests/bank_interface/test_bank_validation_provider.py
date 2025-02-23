from unittest.mock import patch, Mock
from pytest import fixture
import signal
from typing import Generator

from personal_finances.bank_interface.bank_validation_provider import (
    LocalhostValidationProvider,
)


@fixture(autouse=True)
def os_mock() -> Generator[Mock, None, None]:
    with patch("personal_finances.bank_interface.bank_validation_provider.os") as mock:
        yield mock


@fixture(autouse=True)
def subprocess_mock() -> Generator[Mock, None, None]:
    with patch(
        "personal_finances.bank_interface.bank_validation_provider.subprocess"
    ) as mock:
        yield mock


@fixture(autouse=True)
def requests_mock() -> Generator[Mock, None, None]:
    with patch(
        "personal_finances.bank_interface.bank_validation_provider.requests"
    ) as mock:
        yield mock


def test_localhost_validation_provider_scope(
    subprocess_mock: Mock, os_mock: Mock
) -> None:
    with LocalhostValidationProvider():
        pass

    subprocess_mock.Popen.assert_called_with(
        [
            "uvicorn",
            "personal_finances.bank_interface.bank_localhost_validator:app",
            "--reload",
        ],
        preexec_fn=os_mock.setpgrp,
    )
    os_mock.getpgid.assert_called_with(subprocess_mock.Popen.return_value.pid)
    os_mock.killpg.assert_called_with(os_mock.getpgid.return_value, signal.SIGTERM)


def test_localhost_validation_provider_not_validated(requests_mock: Mock) -> None:
    requests_mock.get.return_value.json.return_value = [
        "other-reference",
        "yet-another-one",
    ]
    with LocalhostValidationProvider() as test_provider:
        assert test_provider.is_reference_validated("mock-reference") is False


def test_localhost_validation_provider_validated(requests_mock: Mock) -> None:
    requests_mock.get.return_value.json.return_value = [
        "other-reference",
        "mock-reference",
    ]
    with LocalhostValidationProvider() as test_provider:
        assert test_provider.is_reference_validated("mock-reference") is True


def test_localhost_validation_provides_correct_url() -> None:
    with LocalhostValidationProvider() as test_provider:
        assert (
            test_provider.get_validation_url("mock-reference")
            == "http://127.0.0.1:8000/validations/mock-reference"
        )
