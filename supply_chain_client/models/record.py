import time
from typing import List

from supply_chain_client.models.record_type import RecordType
from supply_chain_client.protobuf.payload_pb2 import *
from supply_chain_client.protobuf.property_pb2 import *
from addressing.supply_chain_addressers.addresser import get_record_address, get_property_address


class Record:

    def __init__(self, record_id: str, record_type: RecordType, properties: List[PropertyValue]):
        self.record_id = record_id
        self.record_type = record_type
        self.properties = properties

    @property
    def name(self):
        return self.record_id

    @property
    def creation_payload(self):
        action = CreateRecordAction(
            record_id=self.record_id,
            record_type=self.record_type.name,
            properties=self.properties
        )

        return SupplyChainPayload(
            action=SupplyChainPayload.Action.CREATE_RECORD,
            timestamp=int(time.time()),
            create_record=action
        ).SerializeToString()

    @property
    def creation_addresses(self):
        addresses = [self.address, self.record_type.address]
        for p in self.record_type.properties:
            addresses.append(get_property_address(self.record_id, p.name))
            addresses.append(get_property_address(self.record_id, p.name, 1))
        return addresses

    @property
    def address(self):
        return get_record_address(self.record_id)
