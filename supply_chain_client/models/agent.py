import time

from supply_chain_client.crypto import get_new_signer
from supply_chain_client.protobuf.payload_pb2 import *
from addressing.supply_chain_addressers.addresser import get_agent_address


class Agent:

    def __init__(self, name: str):
        self.name = name
        self._signer = get_new_signer()
        self._public_key = self._signer.get_public_key().as_hex()

    def sign(self, msg):
        return self._signer.sign(msg)

    def add_agent_payload(self):
        return SupplyChainPayload(
            action=SupplyChainPayload.Action.CREATE_AGENT,
            timestamp=int(time.time()),
            create_agent=CreateAgentAction(name=self.name)
        ).SerializeToString()

    @property
    def address(self):
        return get_agent_address(self._public_key)

    @property
    def pub_key(self):
        return self._public_key