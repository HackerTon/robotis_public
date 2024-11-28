import asyncio
import json
import os
from contextlib import asynccontextmanager
from multiprocessing import Pipe, Queue
from typing import List, Union

import numpy as np
import uvicorn
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, WebSocketException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse

from service.aruco_detector import LapseEngine
from service.frame_collector import LastFrameCollector
from service.logger_service import LoggerService
from service.websocket_manager import WebsocketManager

logger = LoggerService()
connection_manager = WebsocketManager()
frame_pipe = Pipe(False)
visual_pipe = Pipe(False)


device = os.getenv("DEVICE", "cpu")
video_path = os.getenv("VIDEO_PATH", 0)
if video_path == None:
    logger.logger.warning("video_path ENV not provided")
    quit()

logger().warning("Initialization of application")


frame_collector = LastFrameCollector(video_path=video_path)
lapse_engine = LapseEngine()


@asynccontextmanager
async def deepengine(app: FastAPI):
    lapse_engine.run(
        frame_receiver=frame_pipe[0],
        connection_manager=connection_manager,
        visual_sender=visual_pipe[1],
    )
    frame_collector.run(frame_sender=frame_pipe[1])
    lapse_engine.thread.start()
    frame_collector.process.start()
    yield
    lapse_engine.stop()
    lapse_engine.thread.join()
    frame_collector.stop()
    frame_collector.process.join()
    frame_pipe[0].close()
    frame_pipe[1].close()
    visual_pipe[0].close()
    visual_pipe[1].close()
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


@app.get("/visualization")
async def streaming_path():
    def iterfile():
        while True:
            if not visual_pipe[0].poll():
                continue
            data = visual_pipe[0].recv()
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
