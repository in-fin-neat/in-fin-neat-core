from functools import cache
import logging
import boto3
import os
from typing import Any
import boto3.dynamodb
import boto3.dynamodb.table
from pydantic import BaseModel, ValidationError
from schwifty.exceptions import SchwiftyException
from personal_finances.user.user_auth_exceptions import (
    UserNotFound,
    InvalidIban,
    InvalidDynamoResponse,
    UserIdNotInDatabase
)
from schwifty import IBAN
from botocore.exceptions import ClientError

LOGGER = logging.getLogger(__name__)
USER_ID_MIN_LEN = 6
USER_PASSWORD_MIN_LEN = 6


class User(BaseModel):
    userId: str
    password: str
    ibanSet: set[str]


@cache
def _get_user_table() -> Any:
    return boto3.resource("dynamodb").Table(
        os.environ["INFINEAT_DYNAMODB_USER_TABLE_NAME"]
    )


def get_user_password(userId: str) -> str:

    response = _get_user_table().get_item(
        Key={"userId": userId},
    )
    if "Item" not in response:
        raise UserNotFound(f"User not found: {userId}")

    try:
        user = User(**response["Item"])
    except ValidationError as e:
        LOGGER.error(f"Data validation error: {e}")
        raise InvalidDynamoResponse("Invalid data format from DynamoDB")

    return user.password


def get_user_ibans(userId: str) -> set[str]:
    table = _get_user_table()

    try:
        LOGGER.info("Getting user IBAN list...")
        response = table.get_item(Key={"userId": userId})

        if "Item" not in response:
            raise UserNotFound(f"User not found: {userId}")

        user = User(**response["Item"])
        iban_list = user.ibanSet

        LOGGER.info(f"User IBAN list:{iban_list}")
        return iban_list

    except ValidationError as e:
        LOGGER.error(f"Data validation error: {e}")
        raise InvalidDynamoResponse("Invalid data format from DynamoDB")


def update_user_iban(userId: str, newIban: str) -> None:

    LOGGER.info(f"Adding IBAN: {newIban}")
    try:
        IBAN(newIban)
    except SchwiftyException:
        raise InvalidIban("The provided IBAN is invalid")

    try:
        _get_user_table().update_item(
            Key={"userId": userId},
            UpdateExpression="ADD ibanSet :new_iban",
            ExpressionAttributeValues={":new_iban": set([newIban])},
            ConditionExpression="attribute_exists(userId)",
            ReturnValues="UPDATED_NEW"
        )
    except ClientError as e:
        if e.response["Error"]["Code"] == "ConditionalCheckFailedException":
            LOGGER.info(f"response error: {e.response}")
            raise UserIdNotInDatabase(f"userId not found: {userId}")
        else:
            raise Exception(f"Update user iban error: {e.response}")

    LOGGER.info("IBAN added successfully")
