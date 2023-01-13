from difflib import SequenceMatcher
from nordigen_helper import get_reference
from functools import reduce
from enum import Enum
from typing import Tuple, List, Dict
from itertools import chain
import re


class TransactionGroupingType(Enum):
    ReferenceSimilarity = "ReferenceSimilarity"
    Category = "Category"
    AmountRange = "AmountRange"


WORDS_NOT_PART_OF_REFERENCE = [
    ",",
    "*mobi",
    "vdp-",
    "vdc-",
    "vda-",
    "*inet",
    "amanda trojan fenerich",
    "diego tsutsumi",
]


def _clean_reference(reference: str) -> str:
    clean_reference = reference
    for to_remove in WORDS_NOT_PART_OF_REFERENCE:
        clean_reference = clean_reference.replace(to_remove, "")

    clean_reference = re.sub(r"\d{4,}", "", clean_reference)
    return clean_reference


def _get_group_name(group: List[str]) -> str:
    all_references = chain(*[_clean_reference(reference).split(" ") for reference in group])

    sorted_references = sorted(
        reduce(
            lambda frequency, reference: {
                **frequency,
                reference: frequency[reference] + 1,
            },
            all_references,
            {reference: 0 for reference in all_references},
        ).items(),
        key=lambda entry: entry[1],
        reverse=True,
    )

    top_references = sorted_references[:10]
    return " ".join([entry[0] for entry in top_references])


def _get_reference_similarity(ref1: str, ref2: str) -> float:
    return SequenceMatcher(
        None,
        _clean_reference(ref1),
        _clean_reference(ref2),
    ).ratio()


def get_reference_groups(
    transactions: List[Dict], grouping_type: TransactionGroupingType
) -> Tuple[List, Dict]:
    if grouping_type != TransactionGroupingType.ReferenceSimilarity:
        raise NotImplementedError("grouping type not implemented")

    groups = list()
    references = list(map(lambda transaction: get_reference(transaction), transactions))
    for reference in references:
        added = False
        for group_number, group in enumerate(groups):
            similarity_stats = reduce(
                lambda stat, ref_in_group: {
                    "min_ratio": min(
                        stat["min_ratio"],
                        _get_reference_similarity(reference, ref_in_group),
                    ),
                    "max_ratio": max(
                        stat["max_ratio"],
                        _get_reference_similarity(reference, ref_in_group),
                    ),
                },
                group,
                {"min_ratio": 999, "max_ratio": -999},
            )

            if (
                similarity_stats["min_ratio"] > 0.55
                or similarity_stats["max_ratio"] > 0.8
            ):
                group.append(reference)
                added = True
                break

        if not added:
            groups.append([reference])

    group_reference = {
        reference: {"groupName": _get_group_name(group), "groupNumber": group_number}
        for group_number, group in enumerate(groups)
        for reference in group
    }

    return groups, group_reference