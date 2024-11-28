from multiprocessing import Value, Process
from platform import system
from multiprocessing.connection import Connection
import cv2


class LastFrameCollector:
    def __init__(self, video_path: str) -> None:
        self.video_path = video_path
        self.running = Value("b", True)

    def run(self, frame_sender: Connection):
        self.process: Process = Process(
            target=self._start_collection,
            args=[frame_sender],
            daemon=True,
            name="framecollector",
        )

    def stop(self):
        self.running.value = False

    def _start_collection(
        self,
        frame_sender: Connection,
    ):
        system_type = system()

        if system_type == 'Windows':
            camera = cv2.VideoCapture(self.video_path, cv2.CAP_DSHOW)
            camera.set(cv2.CAP_PROP_AUTO_EXPOSURE, 3)
            camera.set(cv2.CAP_PROP_EXPOSURE, -3.0)
            camera.release()
            camera = cv2.VideoCapture(self.video_path, cv2.CAP_DSHOW)
        else:
            camera = cv2.VideoCapture(self.video_path)

        while self.running.value:
            is_running, frame = camera.read()
            if not is_running:
                self.stop()
                break
            frame_sender.send(frame)
        camera.release()
