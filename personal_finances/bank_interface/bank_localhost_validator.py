from fastapi import FastAPI
from typing import Dict, List

app = FastAPI()
VALIDATIONS: List[str] = list()


@app.get("/validations/")
def get_validations() -> List[str]:
    return VALIDATIONS


@app.get("/validations/{institution_id}")
def create_validations(institution_id: str) -> Dict:
    VALIDATIONS.append(institution_id)
    return {"message": "ok"}
