import asyncio
from typing import List

from database import get_table_feed, Database
from models import Agent, RecordType, Record, Property
from websocket_manager import WebSocketManager

from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI, WebSocket, WebSocketDisconnect


app = FastAPI()
db = Database()
manager = WebSocketManager()
updates_queue = asyncio.Queue()


@app.get("/agents", response_model=List[Agent])
async def agents():
    return await db.get_agents()


@app.get("/record_types", response_model=List[RecordType])
async def record_types():
    return await db.get_record_types()


@app.get("/records", response_model=List[Record])
async def records():
    return await db.get_records()


@app.get("/properties/{record_id}", response_model=List[Property])
async def properties(record_id: str):
    return await db.get_properties(record_id)


@app.websocket("/ws/feed")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            _ = await websocket.receive_text()  # Keeping the websocket open
    except WebSocketDisconnect:
        print("WS Client disconnected!")
        manager.disconnect(websocket)


async def table_change_task(table):
    feed = await get_table_feed(table)
    while await feed.fetch_next():
        change = await feed.next()
        await updates_queue.put({"updated_table": table, **change})


async def change_broadcaster_task():
    while True:
        change = await updates_queue.get()
        await manager.broadcast(change)
        updates_queue.task_done()


@app.on_event("startup")
async def tasks_setup():
    asyncio.create_task(table_change_task("blocks")),
    asyncio.create_task(table_change_task("agents")),
    asyncio.create_task(table_change_task("recordTypes")),
    asyncio.create_task(change_broadcaster_task())
    await db.connect()
