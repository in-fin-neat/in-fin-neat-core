from typing import Dict, List, Optional
import uuid


EXPENSE_CATEGORY_REFERENCES = {
    "house": [
        "woodies",
        "ikea",
        "b & q",
        "mortgage",
        "zara",
        "etsy",
        "homestore",
        "home store & more",
        "floor",
        "graydon",
        "furniture",
        "callaghan",
        "emma mat",
        "tile merchant",
        "vidaxlie",
        "johnstown garden centr",
    ],
    "travel": ["travel"],
    "groceries": [
        "dealz",
        "tesco",
        "lidl",
        "dunnes",
        "polonez",
        "aldi",
        "spar",
        "dropchef",
        "hellofresh",
    ],
    "restaurants/pubs": [
        "restaurant",
        "pub",
        "sushi",
        "beer",
        "cafe",
        "bread 41",
        "o briens",
        "wagamama",
        "just eat",
        "costa",
        "gelato",
        "milano",
        "an poitin",
        "pizza",
        "pasta",
        "coffee",
        "avoca",
        "strudel",
        "bunsen",
        "deliveroo",
        "delhi rasoi",
        "annie mays",
        "asahi",
    ],
    "entertainment": [
        "hilfiger",
        "puma",
        "odeon",
        "spotify",
        "entertainment",
        "penneys",
        "ticketmaster",
        "kildare",
        "regatta",
        "amazon prime",
    ],
    "health": ["boots", "drugstore", "pharmacy"],
    "transport": [
        "circle k",
        "freenow",
        "leap card",
        "applegreen",
        "partkingtag",
        "eflow.ie",
        "dublin airport car",
        "payzone park",
    ],
}


INCOME_CATEGORY_REFERENCES = {
    "salary amanda": ["irish manufacturing research", "imr"],
    "salary diego": ["amazon development centre ireland"],
    "income rent": [],
    "income other": [],
}


# Tags are manually included in each bank app
# and have priority over plain transaction references
EXPENSE_CATEGORY_TAGS = {
    "house": ["#house"],
    "travel": ["#travel"],
    "groceries": ["#grocery"],
    "restaurants/pubs": ["#restaurant", "#pub", "#coffee"],
    "entertainment": ["#entertainment"],
    "health": ["#health"],
    "transport": ["#transport"],
}


def _invert_index(category_index: Dict[str, List]) -> Dict[str, str]:
    inverted_index = {}
    for index, entries in category_index.items():
        for entry in entries:
            inverted_index = {**inverted_index, entry: index}
    return inverted_index


def _get_matching_categories(
    reference: str, category_index: Dict[str, List]
) -> List[str]:
    matching_categories = set()
    for reference_keyword, category in category_index.items():
        if reference_keyword in reference:
            matching_categories.add(category)

    return matching_categories


def _resolve_ambiguous_matching_categories(
    matching_categories: List[str], transaction_reference: str
) -> Optional[str]:
    sorted_matching_categories = sorted(matching_categories)

    if len(sorted_matching_categories) > 1:
        print(
            f"""
            ambiguous matching categories, selecting the first
            transaction_reference {transaction_reference}
            matching categories {sorted_matching_categories}
            """
        )

    return next(iter(sorted_matching_categories), None)


def _get_tag_matching_category(transaction_reference: str) -> Optional[str]:
    tag_index = _invert_index(EXPENSE_CATEGORY_TAGS)
    tag_matching_categories = _get_matching_categories(transaction_reference, tag_index)
    return _resolve_ambiguous_matching_categories(
        tag_matching_categories, transaction_reference
    )


def _get_group_ref_matching_category(group_references: List[str]) -> Optional[str]:
    reference_index = _invert_index(
        {**EXPENSE_CATEGORY_REFERENCES, **INCOME_CATEGORY_REFERENCES}
    )
    group_ref_matching_categories = _get_matching_categories(
        "".join(group_references), reference_index
    )
    return _resolve_ambiguous_matching_categories(
        group_ref_matching_categories, "".join(group_references)
    )


def _get_fallback_category(fallback_reference: str) -> str:
    unknown_category_namespace = uuid.UUID("d705d48e-6833-4b96-bb38-5d95a197bb7f")
    return f"unknown.{uuid.uuid5(unknown_category_namespace, fallback_reference)}"


def get_category(
    transaction_reference: str, group_references: List[str], fallback_reference: str
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
        or fallback_reference
    )
