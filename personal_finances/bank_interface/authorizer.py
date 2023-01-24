from fastapi import FastAPI
from typing import Set, Dict

app = FastAPI()
VALIDATIONS: Set[str] = set()


@app.get("/validations/")
def get_validations() -> Set[str]:
    return VALIDATIONS


@app.get("/validations/{institution_id}")
def create_validations(institution_id: str) -> Dict:
    VALIDATIONS.add(institution_id)
    return {"message": "ok"}
