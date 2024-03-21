from abc import ABC, abstractmethod
from nordigen.api import RequisitionsApi
from nordigen.types import RequisitionDto
from pydantic import BaseModel
from typing import List, cast


class Requisitions(BaseModel):
    RequisitionIds: List[str]


EMPTY_REQUISITIONS: Requisitions = Requisitions(RequisitionIds=[])


def gocardless_requisition_adapter(requisitions: List[RequisitionDto]) -> Requisitions:
    return Requisitions.model_validate(
        {
            "RequisitionIds": [
                gocardless_requisition.requisition_id
                for gocardless_requisition in requisitions
            ]
        }
    )


class RequisitionValidator(ABC):
    @abstractmethod
    def is_requisition_valid(self, requisition_id: str) -> bool:
        """
        An interface to validate requisitions
        """
        pass


class GocardlessRequisitionValidator(RequisitionValidator):
    requisition_client: RequisitionsApi

    def __init__(self, requistion_client: RequisitionsApi):
        self.requisition_client = requistion_client

    def is_requisition_valid(self, requisition_id: str) -> bool:
        # https://developer.gocardless.com/bank-account-data/statuses
        return cast(
            bool,
            self.requisition_client.get_requisition_by_id(requisition_id)["status"]
            == "LN",
        )


class RequisitionStore(ABC):
    @abstractmethod
    def save_requisitions(
        self, user_id: str, requisition: Requisitions
    ) -> Requisitions:
        """
        Saves the new requisition and returns the older one
        """
        pass

    @abstractmethod
    def get_last_requisitions(self, user_id: str) -> Requisitions:
        """
        Retrieves the last requisition from the store for a given user id
        """
        pass

    def are_all_requisition_valid(
        self, user_id: str, validator: RequisitionValidator
    ) -> bool:
        last_requisitions = self.get_last_requisitions(user_id)

        if len(last_requisitions.RequisitionIds) == 0:
            return False

        return all(
            validator.is_requisition_valid(requisition_id)
            for requisition_id in last_requisitions.RequisitionIds
        )
