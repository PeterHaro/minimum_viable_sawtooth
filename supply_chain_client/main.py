import base64
import random
from hashlib import sha512
import time
import requests

from sawtooth_sdk.protobuf.transaction_pb2 import TransactionHeader, Transaction
from sawtooth_sdk.protobuf.batch_pb2 import BatchHeader, Batch, BatchList

from addressing.supply_chain_addressers.addresser import FAMILY_NAME, FAMILY_VERSION, get_agent_address, \
    get_record_address, get_property_address

from crypto import get_new_signer
from protobuf.property_pb2 import *
from protobuf.agent_pb2 import *
from protobuf.record_pb2 import *
from supply_chain_client.models.agent import Agent
from supply_chain_client.models.record import Record
from supply_chain_client.models.record_type import RecordType


class SupplyChainClient:

    def __init__(self, api_url: str):
        self._api = api_url
        self._signer = get_new_signer()
        self.pub_key = self._signer.get_public_key().as_hex()

    def get_agent(self, pub_key: str):
        address = get_agent_address(pub_key)
        return self._query_state(address)

    def get_record(self, record_id: str):
        address = get_record_address(record_id)
        return self._query_state(address)

    def get_property(self, record_id, property_name):
        address = get_property_address(record_id, property_name)
        return self._query_state(address)

    def get_property_page(self, record_id, property_name, page_num):
        address = get_property_address(record_id, property_name, page_num)
        return self._query_state(address)

    def add(self, agent: Agent, item=None):
        if item is None:
            item = agent
        payload = item.creation_payload
        header = self._create_transaction_header(
            item.creation_addresses,
            item.creation_addresses,
            payload, agent)
        self._send_payload(payload, header, agent)

    def _send_payload(self, payload, header, agent):
        transaction = Transaction(
            header=header,
            header_signature=agent.sign(header),
            payload=payload)

        batch = self._create_batch(transaction)
        batch_list = BatchList(batches=[batch]).SerializeToString()
        self._send_batches(batch_list)

    def _create_transaction_header(self, inputs, outputs, payload, agent):
        return TransactionHeader(
            family_name=FAMILY_NAME,
            family_version=FAMILY_VERSION,
            inputs=list({agent.address, *inputs}),
            outputs=list({*outputs}),
            signer_public_key=agent.pub_key,
            batcher_public_key=self.pub_key,
            dependencies=[],
            payload_sha512=sha512(payload).hexdigest(),
            nonce=hex(random.randint(0, 2 ** 64))
        ).SerializeToString()

    def _create_batch(self, transaction):
        batch_header = BatchHeader(
            signer_public_key=self.pub_key,
            transaction_ids=[transaction.header_signature],
        ).SerializeToString()

        return Batch(
            header=batch_header,
            header_signature=self._signer.sign(batch_header),
            transactions=[transaction]
        )

    def _send_batches(self, batch_list):
        url = f"{self._api}/batches"
        data = batch_list
        headers = {'Content-Type': 'application/octet-stream'}
        response = requests.post(url, data=data, headers=headers)
        if not response.ok:
            print(f"Error when posting to API.\n Code: {response.status_code}\nText: {response.text}")
        else:
            print(response.text)

    def _query_state(self, address):
        url = f"{self._api}/state/{address}"
        response = requests.get(url)
        if not response.ok:
            print(f"Error when posting to API.\n Code: {response.status_code}\nText: {response.text}")
            return None
        return response.json()


def print_resp(resp, pr):
    f_bytes = base64.b64decode(resp["data"])
    f = pr()
    f.ParseFromString(f_bytes)
    print(f)


if __name__ == "__main__":
    client = SupplyChainClient("http://localhost:8008")

    bond = Agent("Bond, James")
    client.add(bond)

    time.sleep(1)

    temperature_property = PropertySchema(
        name="Temperature",
        data_type=PropertySchema.DataType.NUMBER,
        unit="Celsius")

    weight_property = PropertySchema(
        name="Weight",
        data_type=PropertySchema.DataType.NUMBER,
        unit="kg")

    species_property = PropertySchema(
        name="Species",
        data_type=PropertySchema.DataType.STRING,
        fixed=True,
        required=True)

    fish_pallet = RecordType("FishPallet", [temperature_property])
    client.add(bond, fish_pallet)

    time.sleep(1)

    my_species = PropertyValue(
        name="Species",
        data_type=PropertySchema.DataType.STRING,
        string_value="Cod")

    my_temperature = PropertyValue(
        name="Temperature",
        data_type=PropertySchema.DataType.NUMBER,
        number_value=12
    )

    my_pallet = Record("Palle001", fish_pallet, [my_temperature])
    client.add(bond, my_pallet)

    time.sleep(1.25)

    # TODO: Unwrap containers and pages

    p = client.get_record("Palle001")
    print_resp(p, RecordContainer)

    t = client.get_property("Palle001", "Temperature")
    print_resp(t, PropertyContainer)

    t = client.get_property_page("Palle001", "Temperature", 1)
    print_resp(t, PropertyPageContainer)
