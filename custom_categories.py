from typing import Dict, List
import uuid


EXPENSE_CATEGORIES = {
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
        "asahi"
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
        "amazon prime"
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
        "payzone park"
    ],
}

INCOME_CATEGORIES = {
    "salary amanda": ["irish manufacturing research", "imr"],
    "salary diego": ["amazon development centre ireland"],
    "income rent": [],
    "income other": [],
}


def _get_categories_by_reference(references_by_category: List[Dict]) -> List[Dict]:
    categories_by_reference = {}
    for category, references in {**EXPENSE_CATEGORIES, **INCOME_CATEGORIES}.items():
        for reference in references:
            categories_by_reference = {**categories_by_reference, reference: category}
    return categories_by_reference


def get_category(transaction_reference: str, fallback_reference: str) -> str:
    cat_by_ref = _get_categories_by_reference(
        {**EXPENSE_CATEGORIES, **INCOME_CATEGORIES}
    )

    matching_categories = set()
    for reference_keyword, category in cat_by_ref.items():
        if reference_keyword in transaction_reference:
            matching_categories.add(category)

    sorted_matching_categories = sorted(matching_categories)

    if len(sorted_matching_categories) == 0:
        print(f"""unknown category for reference {transaction_reference}""")
        unknown_category_namespace = uuid.UUID("d705d48e-6833-4b96-bb38-5d95a197bb7f")
        return f"unknown.{uuid.uuid5(unknown_category_namespace, fallback_reference)}"

    if len(sorted_matching_categories) > 1:
        print(
            f"""
            ambiguous matching categories, selecting the first
            transaction_reference {transaction_reference}
            matching categories {sorted_matching_categories}
            """
        )
        pass

    return sorted_matching_categories[0]
