from typing import Dict, Any, List, Optional, Tuple, Type
from unittest.mock import mock_open, patch
import pytest
from personal_finances.config import (
    cache_user_configuration,
    get_user_configuration,
    clear_user_configuration_cache,
    UserConfiguration,
    UserConfigurationParseError,
    UserConfigurationCacheEmpty,
)
import yaml
import copy


def _drop_dict_keys(
    input_dict: Dict[str, Any], keys_to_drop: List[str]
) -> Dict[str, Any]:
    return {k: v for k, v in input_dict.items() if k not in keys_to_drop}


CORRECT_USER_CONFIG_FULL_DICT: Dict[str, Any] = {
    "InternalTransferReferences": ["mock", "internal"],
    "BankProcessingTimeInDays": 2,
    "ExpenseTransactionCodes": ["test", "transaction_code"],
    "FilterReferenceWordsForGrouping": ["non-sense", "characters"],
    "ExpenseCategoryDefinition": [
        {
            "CategoryName": "CookieCashCrunch",
            "CategoryReferences": ["SweetSpendSpree", "DoughDissipation"],
            "CategoryTags": ["#FritterFunds", "#CrumbleCash"],
        },
        {
            "CategoryName": "StormySpendingStreams",
            "CategoryReferences": ["DownpourDollars", "PuddlePayments"],
            "CategoryTags": ["#DrainTheDeposits", "#LiquidateLiquidity"],
        },
    ],
    "IncomeCategoryDefinition": [
        {
            "CategoryName": "InterestIgloo",
            "CategoryReferences": ["SavingsSnowball", "CapitalChill"],
            "CategoryTags": ["#CoolCash", "#FrostyFunds"],
        },
        {
            "CategoryName": "RetroRevenueRomp",
            "CategoryReferences": ["PensionParty", "VintageValueVictory"],
            "CategoryTags": ["#OldieButGoldieGains", "#ClassicCashComeback"],
        },
    ],
}

CORRECT_USER_CONFIG_MISSING_EXPENSE_TRANS_CODE = _drop_dict_keys(
    copy.deepcopy(CORRECT_USER_CONFIG_FULL_DICT), ["ExpenseTransactionCodes"]
)

MISSING_EXPENSE_CATEGORY_DEFINITION: Dict[str, Any] = _drop_dict_keys(
    CORRECT_USER_CONFIG_FULL_DICT, ["ExpenseCategoryDefinition"]
)

INVALID_INTERNAL_TRANSFER_REFERENCES_TYPE: Dict[str, Any] = {
    **copy.deepcopy(CORRECT_USER_CONFIG_FULL_DICT),
    "InternalTransferReferences": "this should've been a list",
}

MISSING_EXPENSE_CATEGORY_HASHTAG = {
    **copy.deepcopy(CORRECT_USER_CONFIG_FULL_DICT),
    "ExpenseCategoryDefinition": [
        {
            "CategoryName": "CookieCashCrunch",
            "CategoryReferences": ["SweetSpendSpree", "DoughDissipation"],
            "CategoryTags": ["Missing", "HashTag", "Here"],
        }
    ],
}

MISSING_INCOME_CATEGORY_HASHTAG = {
    **copy.deepcopy(CORRECT_USER_CONFIG_FULL_DICT),
    "IncomeCategoryDefinition": [
        {
            "CategoryName": "RetroRevenueRomp",
            "CategoryReferences": ["PensionParty", "VintageValueVictory"],
            "CategoryTags": ["Missing", "HashTag", "Here"],
        },
    ],
}

INVALID_YAML: str = """
test_key:
  sub_key: "missing double quotes here
  sub_key2: "should throw exception"
"""


def _yamlify_first_element(list_of_user: List[Tuple]) -> List[Tuple]:
    return [(yaml.dump(first), second, third) for first, second, third in list_of_user]


@pytest.mark.parametrize(
    "test_user_config_yaml, expected_return_value, expected_error",
    [
        *_yamlify_first_element(
            [
                (
                    CORRECT_USER_CONFIG_FULL_DICT,
                    UserConfiguration(**CORRECT_USER_CONFIG_FULL_DICT),
                    None,
                ),
                (
                    CORRECT_USER_CONFIG_MISSING_EXPENSE_TRANS_CODE,
                    UserConfiguration(**CORRECT_USER_CONFIG_MISSING_EXPENSE_TRANS_CODE),
                    None,
                ),
                (
                    MISSING_EXPENSE_CATEGORY_DEFINITION,
                    None,
                    UserConfigurationParseError,
                ),
                (
                    INVALID_INTERNAL_TRANSFER_REFERENCES_TYPE,
                    None,
                    UserConfigurationParseError,
                ),
                (
                    MISSING_EXPENSE_CATEGORY_HASHTAG,
                    None,
                    UserConfigurationParseError,
                ),
                (
                    MISSING_INCOME_CATEGORY_HASHTAG,
                    None,
                    UserConfigurationParseError,
                ),
            ]
        ),
        (
            INVALID_YAML,
            None,
            UserConfigurationParseError,
        ),
    ],
)
def test_cache_user_config(
    test_user_config_yaml: str,
    expected_return_value: Optional[UserConfiguration],
    expected_error: Optional[Type[Exception]],
) -> None:
    file_mock = mock_open(read_data=test_user_config_yaml)
    with patch("personal_finances.config.open", file_mock):
        if expected_error is None:
            assert cache_user_configuration("any-path-here") == expected_return_value
            file_mock.assert_called_with("any-path-here", mode="r")
        else:
            try:
                cache_user_configuration("any-path-here")
            except Exception as e:
                assert isinstance(e, expected_error)
                file_mock.assert_called_with("any-path-here", mode="r")


def test_get_user_config_recache() -> None:
    file_mock_full_dict = mock_open(read_data=yaml.dump(CORRECT_USER_CONFIG_FULL_DICT))
    with patch("personal_finances.config.open", file_mock_full_dict):
        cache_user_configuration("any-path-here")

    assert get_user_configuration().BankProcessingTimeInDays == 2
    assert get_user_configuration().ExpenseTransactionCodes == [
        "test",
        "transaction_code",
    ]

    # re-caching
    file_mock_partial_dict = mock_open(
        read_data=yaml.dump(CORRECT_USER_CONFIG_MISSING_EXPENSE_TRANS_CODE)
    )
    with patch("personal_finances.config.open", file_mock_partial_dict):
        cache_user_configuration("any-path-here")

    assert get_user_configuration().BankProcessingTimeInDays == 2
    assert get_user_configuration().ExpenseTransactionCodes == []


def test_get_user_config_clear_cache() -> None:
    file_mock_full_dict = mock_open(read_data=yaml.dump(CORRECT_USER_CONFIG_FULL_DICT))
    with patch("personal_finances.config.open", file_mock_full_dict):
        cache_user_configuration("any-path-here")

    assert get_user_configuration().BankProcessingTimeInDays == 2
    assert get_user_configuration().ExpenseTransactionCodes == [
        "test",
        "transaction_code",
    ]

    clear_user_configuration_cache()
    with pytest.raises(UserConfigurationCacheEmpty):
        get_user_configuration()
