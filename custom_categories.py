from typing import Dict, List


EXPENSE_CATEGORIES = {
    "house": ["woodies", "ikea", "b & q", "mortgage", "zara", "etsy", "homestore"],
    "travel": ["travel"],
    "food/cleaning": [
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
        "strudel"
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
        "regatta"
    ],
    "health": ["boots", "drugstore", "pharmacy"],
    "transport": ["circle k", "freenow", "leap card", "applegreen", "partkingtag"],
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


def get_category(transaction_reference: str) -> str:
    cat_by_ref = _get_categories_by_reference(
        {**EXPENSE_CATEGORIES, **INCOME_CATEGORIES}
    )

    for reference_keyword, category in cat_by_ref.items():
        if reference_keyword in transaction_reference:
            return category

    return "unknown"


def add_categories_by_reference(transactions: List[Dict]) -> List[Dict]:
    return list(
        map(
            lambda transaction: {
                **transaction,
                "customCategory": get_category(transaction),
            },
            transactions,
        )
    )
