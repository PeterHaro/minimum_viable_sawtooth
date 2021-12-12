from db_config import DB_HOST, DB_PORT, DB_NAME

from rethinkdb import RethinkDB
r = RethinkDB()
r.set_loop_type('asyncio')


async def get_table_feed(table_name: str):
    connection = await _get_connection()
    return await r.table(table_name).changes().run(connection)


async def _get_connection():
    return await r.connect(host=DB_HOST, port=DB_PORT, db=DB_NAME)
