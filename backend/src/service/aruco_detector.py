# from multiprocessing.connection import Connection
import asyncio
import base64
from multiprocessing.connection import Connection
from threading import Thread

from multiprocessing import Queue, Value
from typing import Dict

import cv2
import numpy as np

from service.logger_service import LoggerService
from service.tracking_engine import TrackingEngine
from model.tracking_model import MovingObject
import json

from service.websocket_manager import WebsocketManager


def get_middle(array):
    x = (array[0][0] + array[2][0]) // 2
    y = (array[0][1] + array[2][1]) // 2
    return np.asanyarray([x, y], dtype=int)


class LapseEngine:
    def __init__(self) -> None:
        self.tracking_engine = TrackingEngine()
        self.qr_detector = cv2.aruco.ArucoDetector()
        self.tracking: dict[str, list[float]] = {}
        self.pending: dict[str, list[float]] = {}
        self.running_flag = Value("b", True)

    def stop(self):
        self.running_flag.value = False

    def run(
        self,
        frame_queue: Queue,
        visual_queue: Queue,
        connection_manager: WebsocketManager,
    ):
        self.thread = Thread(
            target=self.infer,
            kwargs={
                "frame_queue": frame_queue,
                "running_flag": self.running_flag,
                "connection_manager": connection_manager,
                "visual_queue": visual_queue,
            },
            daemon=True,
            name="inference",
        )

    def clear(self):
        self.tracking_engine.pending_objects.clear()
        self.tracking_engine.tracking_objects.clear()
        self.tracking.clear()
        self.pending.clear()

    def infer(
        self,
        frame_queue: Queue,
        visual_queue: Queue,
        running_flag,
        connection_manager: WebsocketManager,
    ):
        while running_flag.value:
            if frame_queue.empty():
                continue
            image: np.ndarray = frame_queue.get_nowait()

            corners, ids, _ = self.qr_detector.detectMarkers(image)
            all_moving_objects: list[MovingObject] = []
            if len(corners) != 0:
                for marker_corner, marker_id in zip(corners, ids):
                    marker_id = marker_id.reshape(1)
                    marker_corner = marker_corner.reshape([4, 2])

                    moving_object = MovingObject()
                    moving_object.id = marker_id[0]
                    moving_object.corner = marker_corner

                    all_moving_objects.append(moving_object)

            self.tracking_engine.update(all_moving_objects)

            object_past = self.count_lapse()
            if object_past:
                self.pump_data_into_websocket(connection_manager=connection_manager)

            frame = self.visualisation(image)
            _, img_bytes = cv2.imencode(".jpg", frame)
            data_bytes = np.array(img_bytes).tobytes()
            visual_queue.put_nowait(data_bytes)

    def visualisation(self, frame):
        for moving_object in self.tracking_engine.tracking_objects.values():
            object_in_pending = moving_object.id in self.pending

            # PENDING: RED, UNKNOWN: WHITE
            if object_in_pending:
                color = (0, 0, 255)
            else:
                color = (255, 255, 255)

            frame = cv2.circle(
                frame,
                get_middle(moving_object.corner),
                10,
                (int(color[0]), int(color[1]), int(color[2])),
                5,
            )

        # draw a single line in the middle
        frame = cv2.line(
            frame,
            (0, 1080 // 2 - 5),
            (1920, 1080 // 2 - 5),
            (0, 255, 0),
            thickness=1,
            lineType=cv2.LINE_4,
        )

        frame = cv2.line(
            frame,
            (0, 1080 // 2 + 5),
            (1920, 1080 // 2 + 5),
            (0, 255, 0),
            thickness=1,
            lineType=cv2.LINE_4,
        )
        return frame

    def count_lapse(self) -> bool:
        object_past = False
        for moving_object in self.tracking_engine.tracking_objects.values():
            passed_finish_line = get_middle(moving_object.corner)[1] > (1080 // 2)

            object_in_tracking = moving_object.id in self.tracking
            object_in_pending = moving_object.id in self.pending

            if not passed_finish_line and not object_in_pending:
                self.pending.update(
                    {moving_object.id: [moving_object.last_update_second]}
                )
            elif passed_finish_line and object_in_pending and not object_in_tracking:
                self.pending.pop(moving_object.id)
                self.tracking.update(
                    {moving_object.id: [moving_object.last_update_second]}
                )
                object_past = True
            elif passed_finish_line and object_in_pending and object_in_tracking:
                self.pending.pop(moving_object.id)
                self.tracking[moving_object.id].append(moving_object.last_update_second)
                object_past = True

        return object_past

    def get_lapses(self) -> Dict:
        lapse_per_vehicle = {}
        for id, millis_list in self.tracking.items():
            lapses = []
            for i in range(1, len(millis_list)):
                lapses.append(millis_list[i] - millis_list[i - 1])
            lapse_per_vehicle.update({str(id): lapses})
        return lapse_per_vehicle

    def pump_data_into_websocket(self, connection_manager: WebsocketManager):
        lapse_per_vehicle = self.get_lapses()
        json_data = json.dumps(lapse_per_vehicle)
        asyncio.run(connection_manager.broadcastText(json_data))

    def pump_visualisation_into_websocket(
        self,
        connection_manager: WebsocketManager,
        frame,
    ):
        _, img_bytes = cv2.imencode(".jpg", frame)
        data_bytes = np.array(img_bytes).tobytes()
        asyncio.run(connection_manager.broadcastBytes(base64.encodebytes(data_bytes)))