# Copyright 2017 Intel Corporation
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# -----------------------------------------------------------------------------

from addressing.supply_chain_addressers.addresser import get_address_type
from addressing.supply_chain_addressers.addresser import AddressSpace
from protobuf.supply_chain_protos.agent_pb2 import AgentContainer, Agent
from protobuf.supply_chain_protos.record_pb2 import RecordTypeContainer, RecordType, RecordContainer, Record


CONTAINERS = {
    AddressSpace.AGENT: AgentContainer,
    AddressSpace.RECORD_TYPE: RecordTypeContainer,
    AddressSpace.RECORD: RecordContainer
}

IGNORE = {
    # AddressSpace.OFFER_HISTORY: True
}


def data_to_dicts(address, data):
    """Deserializes a protobuf "container" binary based on its address. Returns
    a list of the decoded objects which were stored at that address.
    """
    data_type = get_address_type(address)

    if IGNORE.get(data_type):
        return []

    try:
        container = CONTAINERS[data_type]
    except KeyError:
        raise TypeError('No container for action type: {}'.format(data_type))

    entries = _parse_proto(container, data).entries
    return [_proto_to_dict(pb) for pb in entries]


def _parse_proto(proto_class, data):
    deserialized = proto_class()
    deserialized.ParseFromString(data)
    return deserialized


def _proto_to_dict(proto):
    result = {}

    for field in proto.DESCRIPTOR.fields:
        key = field.name
        value = getattr(proto, key)

        if field.type == field.TYPE_MESSAGE:
            if field.label == field.LABEL_REPEATED:
                result[key] = [_proto_to_dict(p) for p in value]
            else:
                result[key] = _proto_to_dict(value)

        elif field.type == field.TYPE_ENUM:
            number = int(value)
            name = field.enum_type.values_by_number.get(number).name
            result[key] = name

        else:
            result[key] = value

    return result
