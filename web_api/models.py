from typing import List, Optional

from pydantic import BaseModel


class Agent(BaseModel):
    name: str
    timestamp: int


class PropertySchema(BaseModel):
    name: str
    unit: Optional[str]


class RecordType(BaseModel):
    name: str
    properties: List[PropertySchema]


class Record(BaseModel):
    name: str
