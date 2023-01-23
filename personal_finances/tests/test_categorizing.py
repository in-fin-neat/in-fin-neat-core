import pytest
import re
from typing import List

from personal_finances.transaction.categorizing import get_category


UUID_REGEX = "[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}"


@pytest.mark.parametrize(
    "transaction_reference,group_references,fallback_reference,expected_pattern",
    [
        ("abc", ["abc", "cde"], "some-fallback-ref", rf"unknown\.{UUID_REGEX}"),
        ("abc", ["mortgage", "cde"], "some-fallback-ref", "house"),
        ("#coffee", ["mortgage", "cde"], "some-fallback-ref", "restaurants/pubs"),
        ("abc", ["dealz", "odeon"], "some-fallback-ref", "entertainment"),
    ],
)
def test_get_category(
    transaction_reference: str,
    group_references: List[str],
    fallback_reference: str,
    expected_pattern: str,
):
    assert (
        re.match(
            expected_pattern,
            get_category(transaction_reference, group_references, fallback_reference),
        )
        is not None
    )
