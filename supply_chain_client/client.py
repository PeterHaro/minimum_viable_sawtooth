import base64
import random
from hashlib import sha512
import time
from typing import List, Callable

import requests

from sawtooth_sdk.protobuf.transaction_pb2 import TransactionHeader, Transaction
from sawtooth_sdk.protobuf.batch_pb2 import BatchHeader, Batch, BatchList

from addressing.supply_chain_addressers.addresser import FAMILY_NAME, FAMILY_VERSION, get_agent_address, \
    get_record_address, get_property_address, make_property_address_range

from supply_chain_client.crypto import get_new_signer
from supply_chain_client.protobuf.agent_pb2 import AgentContainer
from supply_chain_client.protobuf.record_pb2 import RecordContainer
from supply_chain_client.protobuf.property_pb2 import PropertyValue, PropertyContainer, PropertyPageContainer
from supply_chain_client.protobuf.payload_pb2 import SupplyChainPayload, UpdatePropertiesAction
from supply_chain_client.models.record_type import RecordTypeItem
from supply_chain_client.models.agent import AgentItem
from supply_chain_client.models.fish_pallet import fish_pallet_type, create_fish_pallet, create_temperature
from supply_chain_client.utils import first_or_none


class SupplyChainClient:

    def __init__(self, api_url: str):
        self._api = api_url
        self._signer = get_new_signer()
        self.pub_key = self._signer.get_public_key().as_hex()

    def get_agent(self, public_key: str):
        """ Get Agent object, as defined in agent.proto, from on public_key.
            Returns None if no agent with the public_key is found. """
        address = get_agent_address(public_key)
        response = self._query_state(address)
        predicate = lambda a: a.public_key == public_key
        return self._instance_from_response(response, AgentContainer, predicate)

    def get_record(self, record_id: str):
        """ Get Record, as defined in record.proto, based on record_id.
            Returns None if no record with the record_id is found. """
        address = get_record_address(record_id)
        response = self._query_state(address)
        predicate = lambda r: r.record_id == record_id
        return self._instance_from_response(response, RecordContainer, predicate)

    def get_property(self, record_id: str, property_name: str):
        """ Get Property, as defined in record.proto from record_id and property_name.
            Returns None if no property is found. """
        address = get_property_address(record_id, property_name)
        response = self._query_state(address)
        predicate = lambda p: p.record_id == record_id and p.name == property_name
        return self._instance_from_response(response, PropertyContainer, predicate)

    def get_property_page(self, record_id: str, property_name: str, page_num: int):
        """ Get PropertyPage, as defined in property.proto, from record_id, property_name, and page_num.
            Returns None if page is not found. """
        address = get_property_address(record_id, property_name, page_num)
        response = self._query_state(address)
        predicate = lambda pp: pp.record_id == record_id and pp.name == property_name
        return self._instance_from_response(response, PropertyPageContainer, predicate)

    def add_agent(self, agent: AgentItem):
        return self._add(agent)

    def add_pallet(self, agent: AgentItem, pallet_id: str, trip_id: int, specie_name: str):
        pallet_item = create_fish_pallet(pallet_id, trip_id, specie_name)
        return self._add(agent, pallet_item)

    def add_record_type(self, agent: AgentItem, record_type: RecordTypeItem):
        return self._add(agent, record_type)

    def _add(self, agent: AgentItem, item=None):
        if item is None:
            item = agent
        payload = item.creation_payload
        header = self._create_transaction_header(
            item.creation_addresses,
            item.creation_addresses,
            payload, agent)
        return self._send_payload(payload, header, agent)

    def update_temperature(self, agent: AgentItem, record_id: str, temperature: int, location: [int, int]):
        temperature_property = create_temperature(temperature, location)
        return self._update_pallet(agent, record_id, [temperature_property])

    def _update_pallet(self, agent: AgentItem, record_id: str, properties: List[PropertyValue]):
        payload = self._create_update_payload(record_id, properties)
        address = [get_record_address(record_id), make_property_address_range(record_id)]
        header = self._create_transaction_header(address, address, payload, agent)
        return self._send_payload(payload, header, agent)

    @staticmethod
    def _create_update_payload(record_id: str, properties: List[PropertyValue]):
        action = UpdatePropertiesAction(record_id=record_id)
        action.properties.extend(properties)
        return SupplyChainPayload(
            action=SupplyChainPayload.Action.UPDATE_PROPERTIES,
            timestamp=int(time.time()),
            update_properties=action
        ).SerializeToString()

    def _send_payload(self, payload, header, agent):
        transaction = Transaction(
            header=header,
            header_signature=agent.sign(header),
            payload=payload)

        batch = self._create_batch(transaction)
        batch_list = BatchList(batches=[batch]).SerializeToString()
        return self._wait_till_processed(self._send_batches(batch_list))

    def _create_transaction_header(self, inputs, outputs, payload, agent):
        return TransactionHeader(
            family_name=FAMILY_NAME,
            family_version=FAMILY_VERSION,
            inputs=list({agent.address, *inputs}),
            outputs=list({*outputs}),
            signer_public_key=agent.public_key,
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
        """ Posts batches to the blockchain (via the sawtooth-rest-api) """
        url = f"{self._api}/batches"
        headers = {'Content-Type': 'application/octet-stream'}
        response = requests.post(url, data=batch_list, headers=headers)
        if not response.ok:
            print(f"Error when posting to API.\n Code: {response.status_code}\nText: {response.text}")
        else:
            return response.json()

    def _wait_till_processed(self, resp, retry=0):
        """ Queries the status link for a transaction until the transaction is no longer marked as "PENDING".
            Max retries are 5, with exponential backoff between them. After that "PENDING" is returned. """
        time.sleep(0.1 + 0.1 * retry)
        r = requests.get(url=resp['link'])
        status = r.json()['data'][0]['status']
        if status == "PENDING" and retry < 5:
            return self._wait_till_processed(resp, retry + 1)
        return status

    def _query_state(self, address: str):
        """ Gets the state stored at an address on the blockchain.
            Returns None if no state is stored for the provided address. """
        response = requests.get(f"{self._api}/state/{address}")
        if response.ok:
            return response.json()
        elif response.status_code == 404:
            return None
        else:
            print(f"Some error occurred when posting to API.\nCode: {response.status_code}\nText: {response.text}")
            return None

    @staticmethod
    def _instance_from_response(response, container_class, predicate: Callable):
        """ Gets correct instance from a container (eg. a Property from a PropertyContainer) """
        if response is not None:
            container = SupplyChainClient._response_to_container(response, container_class)
            return first_or_none(predicate, container.entries)
        else:
            return None

    @staticmethod
    def _response_to_container(response, container_class):
        """ Converts a state response into an instance of a container class defined in the protos. """
        container_bytes = base64.b64decode(response["data"])
        container = container_class()
        container.ParseFromString(container_bytes)
        return container


if __name__ == "__main__":
    cli = SupplyChainClient("http://localhost:8008")
    test_agent = AgentItem("agent0001")

    cli.add_agent(test_agent)
    cli.add_record_type(test_agent, fish_pallet_type)
    cli.add_pallet(test_agent, "p1", 2, "Cod")
    cli.update_temperature(test_agent, "p1", 11, [69, 12])
    cli.update_temperature(test_agent, "p1", 12, [70, 12])

    print(cli.get_agent(test_agent.public_key))
    print(cli.get_record("p1"))
    print(cli.get_property("p1", "Specie"))
    print(cli.get_property("p1", "Temperature"))
    print(cli.get_property_page("p1", "Temperature", 1))
