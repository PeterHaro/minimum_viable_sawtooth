import time

from supply_chain_client.crypto import get_new_signer
from supply_chain_client.protobuf.payload_pb2 import SupplyChainPayload, CreateAgentAction
from addressing.supply_chain_addressers.addresser import get_agent_address


class AgentItem:

    def __init__(self, name: str):
        self.name = name
        self._signer = get_new_signer()
        self._public_key = self._signer.get_public_key().as_hex()

    def sign(self, msg):
        return self._signer.sign(msg)

    @property
    def creation_payload(self):
        return SupplyChainPayload(
            action=SupplyChainPayload.Action.CREATE_AGENT,
            timestamp=int(time.time()),
            create_agent=CreateAgentAction(name=self.name)
        ).SerializeToString()

    @property
    def creation_addresses(self):
        return [self.address]

    @property
    def address(self):
        return get_agent_address(self._public_key)

    @property
    def public_key(self):
        return self._public_key
