from enum import IntEnum
from typing import List, Optional

from pydantic import BaseModel

# Models are based on protobufs in project_root/protos/


# class DataType(IntEnum):
#     TYPE_UNSET = 0
#     BYTES = 1
#     BOOLEAN = 2
#     NUMBER = 3
#     STRING = 4
#     ENUM = 5
#     STRUCT = 6
#     LOCATION = 7


class Reporter(BaseModel):
    public_key: str
    authorized: bool
    index: int


class AssociatedAgent(BaseModel):
    agent_id: str
    timestamp: int


class Agent(BaseModel):
    public_key: str
    name: str
    timestamp: int


class PropertySchema(BaseModel):
    name: str
    data_type: str
    required: bool = False
    fixed: bool = False
    delayed: bool = False
    number_exponent: Optional[int]
    enum_options: Optional[List[str]]
    struct_properties: Optional[List['PropertySchema']]
    unit: Optional[str]


PropertySchema.update_forward_refs()


class Record(BaseModel):
    record_id: str
    record_type: str
    owners: List[AssociatedAgent]
    custodians: List[AssociatedAgent]
    final: bool = False


class RecordType(BaseModel):
    name: str
    properties: List[PropertySchema]


class Property(BaseModel):
    name: str
    record_id: str
    data_type: str
    reporters: List[Reporter]
    current_page: int = 1
    wrapped: bool = False
    fixed: Optional[bool]
    number_exponent: Optional[int]
    enum_options: Optional[List[str]]
    struct_properties: Optional[List[PropertySchema]]
    unit: Optional[str]
