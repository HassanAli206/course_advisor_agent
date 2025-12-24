from pydantic import BaseModel
from typing import List, Optional, Union, Any, Dict

class ChatRequest(BaseModel):
    student_id: str  # This was missing!
    message: str

class ChatResponse(BaseModel):
    reply: Union[Dict[str, Any], List[Dict[str, Any]], str, List[str]]

class Config:
    arbitrary_types_allowed = True

class ValidationError(BaseModel):
    loc: List[str]
    msg: str
    type: str

class HTTPValidationError(BaseModel):
    detail: List[ValidationError]