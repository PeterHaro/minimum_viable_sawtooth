import time
from typing import List

from supply_chain_client.protobuf.payload_pb2 import *
from supply_chain_client.protobuf.property_pb2 import *
from addressing.supply_chain_addressers.addresser import get_record_type_address


class RecordType:

    def __init__(self, name: str, properties: List[PropertySchema]):
        self.name = name
        self.properties = properties

    def add_record_payload(self):
        action = CreateRecordTypeAction(name=self.name)
        for p in self.properties:
            action.properties.append(p)

        payload = SupplyChainPayload(
            action=SupplyChainPayload.Action.CREATE_RECORD_TYPE,
            timestamp=int(time.time()),
            create_record_type=action
        )
        return payload.SerializeToString()

    # def add_properties(self, payload):
    #     for p in self.properties:
    #         payload.properties.append(p)
    #     return payload

    @property
    def address(self):
        return get_record_type_address(self.name)
