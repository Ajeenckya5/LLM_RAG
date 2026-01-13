from pydantic import BaseModel
from typing import Optional, List


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class QueryRequest(BaseModel):
    query: str


class SourceItem(BaseModel):
    email_id: int
    subject: Optional[str] = None
    sender: Optional[str] = None
    sent_at: Optional[str] = None
    link: str
    snippet: str


class QueryResponse(BaseModel):
    answer: str
    sources: List[SourceItem]

