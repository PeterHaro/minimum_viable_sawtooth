from fastapi import HTTPException

from db_config import DB_HOST, DB_PORT, DB_NAME

from rethinkdb import RethinkDB

from models import VALUES_LOOKUP, ReportedValue

r = RethinkDB()
r.set_loop_type('asyncio')


async def get_table_feed(table_name: str):
    connection = await _get_connection()
    return await r.table(table_name).changes().run(connection)


async def _get_connection():
    return await r.connect(host=DB_HOST, port=DB_PORT, db=DB_NAME)


class Database:

    def __init__(self):
        self.connection = None

    async def connect(self):
        self.connection = await _get_connection()

    async def get_agents(self):
        return await r.table('agents') \
            .without('delta_id', 'start_block_num', 'end_block_num') \
            .coerce_to('array').run(self.connection)

    async def get_record_types(self):
        return await r.table('recordTypes') \
            .without('delta_id', 'start_block_num', 'end_block_num') \
            .coerce_to('array').run(self.connection)

    async def get_records(self):
        return await r.table('records') \
            .without('delta_id', 'start_block_num', 'end_block_num') \
            .coerce_to('array').run(self.connection)

    async def get_properties(self, record_id: str):
        properties = await r.table('properties') \
            .filter(r.row['record_id'] == record_id) \
            .without('delta_id', 'start_block_num', 'end_block_num') \
            .coerce_to('array').run(self.connection)

        return properties

    async def get_property(self, record_id: str, property_name: str):
        prop = await r.table('properties') \
            .filter(r.row['name'] == property_name and r.row['record_id'] == record_id) \
            .without('delta_id', 'start_block_num', 'end_block_num') \
            .coerce_to('array').run(self.connection)

        try:
            return prop[0]
        except IndexError:
            raise HTTPException(
                status_code=404, detail=f'Property ({property_name}) or record_id ({record_id}) not found.')

    async def get_property_type(self, record_id: str, property_name: str):
        prop = await self.get_property(record_id, property_name)
        return prop["data_type"]

    async def get_property_page(self, record_id, property_name, page_num=1):
        property_dtype = await self.get_property_type(record_id, property_name)
        value_key = VALUES_LOOKUP[property_dtype]
        excludes = {'reported_values': {v: True for v in VALUES_LOOKUP.values()}}
        excludes['reported_values'].pop(value_key)

        resp = await r.table('propertyPages') \
            .filter(
                r.row['record_id'] == record_id and
                r.row['name'] == property_name and
                r.row['page_num'] == page_num
            ) \
            .without('delta_id', 'start_block_num', 'end_block_num') \
            .without(excludes) \
            .coerce_to('array') \
            .run(self.connection)

        try:
            return resp[0]
        except IndexError:
            raise HTTPException(status_code=404, detail=f"Page {page_num} not found.")
