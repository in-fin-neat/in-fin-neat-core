from functools import cache
import json
import logging
import boto3
import os
from typing import Any
import boto3.dynamodb
import boto3.dynamodb.table
from decorator import decorator
from package.botocore.exceptions import ClientError
from personal_finances.user.user_auth_exceptions import (
    UserNotFound,
    InvalidIban,
    InvalidDynamoResponse,
)
from stdnum import iban

LOGGER = logging.getLogger(__name__)
USER_ID_MIN_LEN = 6
USER_PASSWORD_MIN_LEN = 6


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

    user = response["Item"]
    if "password" not in user or "userId" not in user:
        raise InvalidDynamoResponse

    return str(user["password"])


def get_user_ibans(userId: str) -> str:
    table = _get_user_table()

    try:
        response = table.get_item(Key={"userId": userId})
        item = response.get("Item", {})
        iban_list = item.get("userIbanList", [])
        # check user returned with pydantic 
        
        return json.dumps(iban_list) # return raw lists instead json

    except ClientError as e:
        print(f"Failed to retrieve item: {e.response['Error']['Message']}")
        return ""


def update_user_iban(userId: str, newIban: str) -> None:

    if not iban.is_valid(newIban):
        raise (InvalidIban)
    #todo:: check the string pattern
    table = _get_user_table()
    
    response = table.get_item(Key={"userId": userId})
    iban_list = response.get("Item", {}).get("ibanList", [])

    #todo:: check if the user item is valid using pydantic
    if newIban in iban_list:
        logging.info("IBAN already exists for the user.")
        return

    iban_list.append(newIban) #change to set

    try:
        response = table.update_item(
            Key={"userId": userId},
            UpdateExpression="SET ibanList = :updated_list",
            ExpressionAttributeValues={":updated_list": iban_list},
            ReturnValues="UPDATED_NEW",
        )
        logging.info("IBAN added successfully:", response)

    except ClientError as e:
        logging.error(f"Failed to update item: {e.response['Error']['Message']}")
        raise (e)
