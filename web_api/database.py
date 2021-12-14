from db_config import DB_HOST, DB_PORT, DB_NAME

from rethinkdb import RethinkDB
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
            .without('public_key', 'delta_id',
                     'start_block_num', 'end_block_num') \
            .coerce_to('array').run(self.connection)

    async def get_record_types(self):
        return await r.table('recordTypes') \
            .without('delta_id', 'start_block_num', 'end_block_num') \
            .coerce_to('array').run(self.connection)

    async def get_records(self):
        return await r.table('records') \
            .without('delta_id', 'start_block_num', 'end_block_num') \
            .coerce_to('array').run(self.connection)
