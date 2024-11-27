import asyncio
import json
import os
from contextlib import asynccontextmanager
from multiprocessing import Pipe, Queue
from typing import List, Union

from fastapi.responses import StreamingResponse
import numpy as np
import uvicorn
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, WebSocketException
from fastapi.middleware.cors import CORSMiddleware

from service.aruco_detector import LapseEngine
from service.frame_collector import LastFrameCollector
from service.logger_service import LoggerService
from service.websocket_manager import WebsocketManager

logger = LoggerService()
connection_manager = WebsocketManager()
frame_queue: Queue = Queue()
visual_queue: Queue = Queue()


device = os.getenv("DEVICE", "cpu")
video_path = os.getenv("VIDEO_PATH", 0)
if video_path == None:
    logger.logger.warning("video_path ENV not provided")
    quit()

logger().warning("Initialization of application")


collector = LastFrameCollector(video_path=video_path)
lapse_engine = LapseEngine()


@asynccontextmanager
async def deepengine(app: FastAPI):
    lapse_engine.run(
        frame_queue=frame_queue,
        connection_manager=connection_manager,
        visual_queue=visual_queue,
    )
    collector.start(queue=frame_queue)
    lapse_engine.thread.start()
    collector.process.start()
    yield
    lapse_engine.stop()
    lapse_engine.thread.join()
    collector.stop()
    collector.process.join()
    LoggerService().logger.warning("Done stopping inference and collector")


app = FastAPI(lifespan=deepengine)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def status_path():
    return "Hello world, I am online"


@app.delete("/")
def delete_all():
    lapse_engine.clear()
    return {"status": "done"}


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await connection_manager.connect(websocket)
    try:
        while True:
            lapse_per_vehicle = lapse_engine.get_lapses()
            json_data = json.dumps(lapse_per_vehicle)
            await websocket.send_text(json_data)
            await websocket.receive_text()
    except WebSocketDisconnect:
        connection_manager.disconnect(websocket)


# @app.websocket("/wsvideo")
# async def websocket_video_endpoint(websocket: WebSocket):
#     await video_connection_manager.connect(websocket)
#     try:
#         while True:
#             await websocket.receive_text()
#     except WebSocketDisconnect:
#         video_connection_manager.disconnect(websocket)


@app.get("/visualization")
async def streaming_path():
    def iterfile():
        while True:
            if visual_queue.empty():
                continue
            data = visual_queue.get_nowait()
            if not data:
                continue

            yield b"--frame\r\n" b"Content-Type: image/jpeg\r\n\r\n" + data + b"\r\n"

    return StreamingResponse(
        iterfile(),
        media_type="multipart/x-mixed-replace;boundary=frame",
    )


if __name__ == "__main__":
    uvicorn.run(
        app=app,
        host="0.0.0.0",
        port=8000,
    )
