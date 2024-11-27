from fastapi import WebSocket


class WebsocketManager:
    def __init__(self) -> None:
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcastText(self, data_json_text: str):
        for connection in self.active_connections:
            await connection.send_text(data_json_text)

    async def broadcastBytes(self, data_bytes: bytes):
        for connection in self.active_connections:
            await connection.send_bytes(data_bytes)
