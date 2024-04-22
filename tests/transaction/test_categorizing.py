from unittest.mock import Mock, patch
import pytest
import re
from typing import List, Generator

from personal_finances.config import CategoryDefinition
from personal_finances.transaction.categorizing import get_category, _get_expense_category_references, _get_expense_category_tags, _get_income_category_references


UUID_REGEX = "[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}"


@pytest.fixture(autouse=True)
def user_config_mock() -> Generator[Mock, None, None]:
    with patch(
        "personal_finances.transaction.categorizing.get_user_configuration"
    ) as u_mock:
        _get_expense_category_references.cache_clear(),
        _get_expense_category_tags.cache_clear()
        _get_income_category_references.cache_clear()
        u_mock.return_value.ExpenseCategoryDefinition = [
            CategoryDefinition(
                CategoryName="house",
                CategoryReferences=["ikea", "dealz"],
                CategoryTags=[],
            ),
            CategoryDefinition(
                CategoryName="restaurants/pubs",
                CategoryReferences=["some-fancy-pub"],
                CategoryTags=["#coffee", "#restaurant"],
            ),
            CategoryDefinition(
                CategoryName="entertainment",
                CategoryReferences=["odeon"],
                CategoryTags=[],
            ),
        ]

        u_mock.return_value.IncomeCategoryDefinition = []
        yield u_mock


@pytest.mark.parametrize(
    "transaction_reference,group_references,fallback_reference,expected_pattern",
    [
        (
            "abc",
            ["abc", "cde"],
            "some-fallback-ref",
            rf"some-fallback-ref\.{UUID_REGEX}",
        ),
        ("abc", ["ikea", "cde"], "some-fallback-ref", "house"),
        ("#coffee", ["mortgage", "cde"], "some-fallback-ref", "restaurants/pubs"),
        ("abc", ["dealz", "odeon"], "some-fallback-ref", "entertainment"),
    ],
)
def test_get_category(
    transaction_reference: str,
    group_references: List[str],
    fallback_reference: str,
    expected_pattern: str,
) -> None:
    result = get_category(transaction_reference, group_references, fallback_reference)
    assert (
        re.match(
            expected_pattern,
            result,
        )
        is not None
    )
