from typing import Dict, Iterable, List, Optional, Set, Callable, Tuple
import uuid
import logging
from ..config import get_user_configuration, CategoryDefinition
from functools import cache


LOGGER = logging.getLogger(__name__)


def _get_expense_category_references() -> Dict[str, List[str]]:
    return _index_field_by_category_name(
        tuple(get_user_configuration().ExpenseCategoryDefinition),
        lambda category_definition: category_definition.CategoryReferences,
    )


def _get_expense_category_tags() -> Dict[str, List[str]]:
    return _index_field_by_category_name(
        tuple(get_user_configuration().ExpenseCategoryDefinition),
        lambda category_definition: category_definition.CategoryTags,
    )


def _get_income_category_references() -> Dict[str, List[str]]:
    return _index_field_by_category_name(
        tuple(get_user_configuration().IncomeCategoryDefinition),
        lambda category_definition: category_definition.CategoryReferences,
    )


@cache
def _index_field_by_category_name(
    category_definitions: Tuple[CategoryDefinition],  # tuple is hashable for caching
    field: Callable[[CategoryDefinition], List[str]],
) -> Dict[str, List[str]]:
    return {cat_def.CategoryName: field(cat_def) for cat_def in category_definitions}


def _invert_index(category_index: Dict[str, List]) -> Dict[str, str]:
    inverted_index: Dict = {}
    for index, entries in category_index.items():
        for entry in entries:
            inverted_index = {**inverted_index, entry: index}
    return inverted_index


def _get_matching_categories(
    reference: str, category_index: Dict[str, str]
) -> List[str]:
    matching_categories: Set[str] = set()
    for reference_keyword, category in category_index.items():
        if reference_keyword in reference:
            matching_categories.add(category)

    return list(matching_categories)


def _resolve_ambiguous_matching_categories(
    matching_categories: List[str], transaction_reference: str
) -> Optional[str]:
    if len(matching_categories) == 0:
        return None

    sorted_matching_categories = sorted(matching_categories)

    if len(sorted_matching_categories) > 1:
        LOGGER.info(
            f"""
            ambiguous matching categories, selecting the first
            transaction_reference {transaction_reference}
            matching categories {sorted_matching_categories}
            """
        )

    return sorted_matching_categories[0]


def _get_tag_matching_category(transaction_reference: str) -> Optional[str]:
    tag_index = _invert_index(_get_expense_category_tags())
    tag_matching_categories = _get_matching_categories(transaction_reference, tag_index)
    return _resolve_ambiguous_matching_categories(
        tag_matching_categories, transaction_reference
    )


def _get_group_ref_matching_category(group_references: Iterable[str]) -> Optional[str]:
    reference_index = _invert_index(
        {
            **_get_expense_category_references(),
            **_get_income_category_references(),
        }
    )
    group_ref_matching_categories = _get_matching_categories(
        "".join(group_references), reference_index
    )
    return _resolve_ambiguous_matching_categories(
        group_ref_matching_categories, "".join(group_references)
    )


def _get_fallback_category(fallback_reference: str) -> str:
    unknown_category_namespace = uuid.UUID("d705d48e-6833-4b96-bb38-5d95a197bb7f")
    return (
        f"{fallback_reference}."
        + f"{uuid.uuid5(unknown_category_namespace, fallback_reference)}"
    )


def get_category(
    transaction_reference: str, group_references: Iterable[str], fallback_reference: str
) -> str:
    """
    Returns matching category given references in this order:
    1. Categories matching tags
    2. Categories matching group references
    3. Fallback category using given fallback_reference
    """
    return (
        _get_tag_matching_category(transaction_reference)
        or _get_group_ref_matching_category(group_references)
        or _get_fallback_category(fallback_reference)
    )
