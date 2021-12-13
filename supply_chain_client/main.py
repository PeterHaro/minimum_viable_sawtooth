import base64
import random
from hashlib import sha512
import time
import requests

from sawtooth_sdk.protobuf.transaction_pb2 import TransactionHeader, Transaction
from sawtooth_sdk.protobuf.batch_pb2 import BatchHeader, Batch, BatchList

from addressing.supply_chain_addressers.addresser import FAMILY_NAME, FAMILY_VERSION, get_agent_address

from crypto import get_new_signer
from protobuf.payload_pb2 import *
from protobuf.property_pb2 import *
from protobuf.agent_pb2 import *
from supply_chain_client.models.agent import Agent
from supply_chain_client.models.record_type import RecordType


class SupplyChainClient:

    def __init__(self, api_url: str):
        self._api = api_url
        self._signer = get_new_signer()
        self.pub_key = self._signer.get_public_key().as_hex()

    def get_agent(self, pub_key: str):
        address = get_agent_address(pub_key)
        return self.query_state(address)

    def add_agent(self, agent: Agent):
        payload = agent.add_agent_payload()
        header = self.create_transaction_header(agent.address, payload, agent)
        self.send_payload(payload, header, agent)

    def add_record(self, agent: Agent, record):
        pass

    def add_record_type(self, record_type: RecordType, agent: Agent):
        payload = record_type.add_record_payload()
        header = self.create_transaction_header(record_type.address, payload, agent)
        self.send_payload(payload, header, agent)

    def send_payload(self, payload, header, agent):
        transaction = Transaction(
            header=header,
            header_signature=agent.sign(header),
            payload=payload)

        batch = self.create_batch(transaction)
        batch_list = BatchList(batches=[batch]).SerializeToString()
        self.send_batches(batch_list)

    def create_transaction_header(self, address, payload, agent):
        return TransactionHeader(
            family_name=FAMILY_NAME,
            family_version=FAMILY_VERSION,
            inputs=[address, agent.address],
            outputs=[address],
            signer_public_key=agent.pub_key,
            batcher_public_key=self.pub_key,
            dependencies=[],
            payload_sha512=sha512(payload).hexdigest(),
            nonce=hex(random.randint(0, 2 ** 64))
        ).SerializeToString()

    def create_batch(self, transaction):
        batch_header = BatchHeader(
            signer_public_key=self.pub_key,
            transaction_ids=[transaction.header_signature],
        ).SerializeToString()

        return Batch(
            header=batch_header,
            header_signature=self._signer.sign(batch_header),
            transactions=[transaction]
        )

    @staticmethod
    def create_add_agent_payload(name):
        return SupplyChainPayload(
            action=SupplyChainPayload.Action.CREATE_AGENT,
            timestamp=int(time.time()),
            create_agent=CreateAgentAction(name=name)
        ).SerializeToString()

    @staticmethod
    def create_add_record_type_payload(name):
        return SupplyChainPayload(
            action=SupplyChainPayload.Action.CREATE_AGENT,
            timestamp=int(time.time()),
            create_record_type=CreateRecordTypeAction(name=name)
        ).SerializeToString()

    def send_batches(self, batch_list):
        url = f"{self._api}/batches"
        data = batch_list
        headers = {'Content-Type': 'application/octet-stream'}
        response = requests.post(url, data=data, headers=headers)
        if not response.ok:
            print(f"Error when posting to API.\n Code: {response.status_code}\nText: {response.text}")
        else:
            print(response.text)

    def query_state(self, address):
        url = f"{self._api}/state/{address}"
        response = requests.get(url)
        if not response.ok:
            print(f"Error when posting to API.\n Code: {response.status_code}\nText: {response.text}")
            return None
        return response.json()


def print_agent(resp):
    f_bytes = base64.b64decode(resp["data"])
    f = AgentContainer()
    f.ParseFromString(f_bytes)
    print(f)


if __name__ == "__main__":
    client = SupplyChainClient("http://localhost:8008")

    bond = Agent("Bond, James")
    client.add_agent(bond)

    time.sleep(1.25)

    temperature_property = PropertySchema(
        name="temperature",
        data_type=3,  # PropertySchema.DataType.NUMBER,
        unit="Celsius"
    )

    fish_pallet = RecordType("FishPallet", [temperature_property])
    client.add_record_type(fish_pallet, bond)

    # time.sleep(1)
    # resp = client.get_agent(pub)
    # print("Before update:")
    # print_agent(resp)

    # client.add_update_to_fesk(fesk_name, 12)
    # time.sleep(1)
    # fesk_resp = client.get_agent(fesk_name)
    # print("After update:")
    # print_fesk(fesk_resp)
