from pydantic import BaseModel
from typing import Literal


class ClassificationResult(BaseModel):
    id: str
    category: Literal["MAJOR", "NON-MAJOR"]


class ClassificationResponse(BaseModel):
    results: list[ClassificationResult]
