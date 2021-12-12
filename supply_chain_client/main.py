import base64
import os
import random
import sys
from hashlib import sha512
import time
import requests

TOP_DIR = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
sys.path.insert(0, os.path.join(TOP_DIR, 'protobuf'))

from sawtooth_sdk.protobuf.transaction_pb2 import TransactionHeader, Transaction
from sawtooth_sdk.protobuf.batch_pb2 import BatchHeader, Batch, BatchList
from sawtooth_signing import create_context
from sawtooth_signing import CryptoFactory

from addressing.supply_chain_addressers.addresser import FAMILY_NAME, FAMILY_VERSION, get_agent_address
from protobuf.supply_chain_protos.payload_pb2 import SupplyChainPayload, CreateAgentAction
from protobuf.supply_chain_protos.agent_pb2 import AgentContainer


# TODO: Handle signing properly
context = create_context('secp256k1')
private_key = context.new_random_private_key()
signer = CryptoFactory(context).new_signer(private_key)
pub = signer.get_public_key().as_hex()


class SupplyChainClient:

    def __init__(self, api_url: str):
        self._api = api_url

    def get_agent(self, pub_key: str):
        address = get_agent_address(pub_key)
        return self.query_state(address)

    def add_agent(self, pub_key, name):
        payload = self.create_add_agent_payload(name)
        address = get_agent_address(pub_key)
        header = self.create_transaction_header(address, payload)
        self.send_payload(payload, header)

    # def add_update_to_agent(self, pub_key, temperature):
    #     payload = self.create_update_agent_payload(name, temperature)
    #     address = get_agent_address(pub_key)
    #     header = self.create_transaction_header(get_agent_address(name), payload)
    #     self.send_payload(payload, header)

    def send_payload(self, payload, header):
        transaction = Transaction(
            header=header,
            header_signature=signer.sign(header),
            payload=payload)

        batch = self.create_batch(transaction)
        batch_list = BatchList(batches=[batch]).SerializeToString()
        self.send_batches(batch_list)

    @staticmethod
    def create_transaction_header(address, payload):
        return TransactionHeader(
            family_name=FAMILY_NAME,
            family_version=FAMILY_VERSION,
            inputs=[address],
            outputs=[address],
            signer_public_key=pub,
            batcher_public_key=pub,
            dependencies=[],
            payload_sha512=sha512(payload).hexdigest(),
            nonce=hex(random.randint(0, 2 ** 64))
        ).SerializeToString()

    @staticmethod
    def create_batch(transaction):
        batch_header = BatchHeader(
            signer_public_key=pub,
            transaction_ids=[transaction.header_signature],
        ).SerializeToString()

        return Batch(
            header=batch_header,
            header_signature=signer.sign(batch_header),
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
    def create_update_fesk_payload(name, temperature):
        now = int(time.time())
        update = Update(
            timestamp=now,
            temperature=temperature)

        action = Action(
            action_type=ValidActions.UPDATE,
            update=update)

        return FeskPayload(
            name=name,
            timestamp=now,
            action=action,
            public_key=pub
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

    agent_name = "agent007"

    client = SupplyChainClient("http://localhost:8008")
    client.add_agent(pub, agent_name)

    # time.sleep(1)
    # resp = client.get_agent(pub)
    # print("Before update:")
    # print_agent(resp)

    # client.add_update_to_fesk(fesk_name, 12)
    # time.sleep(1)
    # fesk_resp = client.get_agent(fesk_name)
    # print("After update:")
    # print_fesk(fesk_resp)
