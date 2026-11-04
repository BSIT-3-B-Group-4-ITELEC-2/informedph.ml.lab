from pydantic import BaseModel


class SummaryResult(BaseModel):
    title: str
    summary: str
    explantion: str


class SummarizationResponse(BaseModel):
    results: list[SummaryResult]
