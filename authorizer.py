from fastapi import FastAPI
from typing import Set

app = FastAPI()
VALIDATIONS: Set[str] = set()


@app.get("/validations/")
def get_validations():
    return VALIDATIONS


@app.get("/validations/{institution_id}")
def create_validations(institution_id: str):
    VALIDATIONS.add(institution_id)
    return {"message": "ok"}
