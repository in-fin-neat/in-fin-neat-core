from typing import List, Optional
import yaml
from pydantic import BaseModel, field_validator
import logging


LOGGER = logging.getLogger(__name__)


class UserConfigurationParseError(Exception):
    pass


class UserConfigurationCacheEmpty(Exception):
    pass


class CategoryDefinition(BaseModel):
    CategoryName: str
    CategoryReferences: List[str]
    CategoryTags: List[str]

    @field_validator("CategoryTags")
    @classmethod
    def tags_begin_with_hashtag(cls, category_tags: List[str]) -> List[str]:
        for category_tag in category_tags:
            assert category_tag[0] == "#"
        return category_tags


class UserConfiguration(BaseModel):
    """
    A direct map of configurations read by YAML file, please refer to
    docs/user_configuration_file.md for a more detailed documentation.
    """

    # Required Attributes
    InternalTransferReferences: List[str]
    BankProcessingTimeInDays: int
    FilterReferenceWordsForGrouping: List[str]
    ExpenseCategoryDefinition: List[CategoryDefinition]
    IncomeCategoryDefinition: List[CategoryDefinition]

    # Optional Attributes
    ExpenseTransactionCodes: List[str] = []


USER_CONFIG_CACHE: Optional[UserConfiguration] = None


def _parse_yaml_content(user_yaml_content: str) -> UserConfiguration:
    try:
        LOGGER.debug(f"parsing user configuration: {user_yaml_content}")
        user_content_dict = yaml.safe_load(user_yaml_content)
        return UserConfiguration.model_validate(user_content_dict)
    except Exception as e:
        LOGGER.error(e)
        raise UserConfigurationParseError from e


def cache_user_configuration(user_config_yaml_path: str) -> UserConfiguration:
    """
    Opens, reads, (re-)caches the singleton and returns the
    parsed contents of the input file path.
    """
    global USER_CONFIG_CACHE
    with open(user_config_yaml_path, mode="r") as user_config_file:
        USER_CONFIG_CACHE = _parse_yaml_content(user_config_file.read())
        return USER_CONFIG_CACHE


def clear_user_configuration_cache() -> None:
    global USER_CONFIG_CACHE
    USER_CONFIG_CACHE = None


def get_user_configuration() -> UserConfiguration:
    """
    Returns previously cached, through `cache_user_configuration` function,
    object UserConfiguration.
    """
    global USER_CONFIG_CACHE

    if USER_CONFIG_CACHE is None:
        raise UserConfigurationCacheEmpty(
            "call cache_user_confguration before get_user_configuration"
        )

    return USER_CONFIG_CACHE
