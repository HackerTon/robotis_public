from multiprocessing import Queue, Value
from threading import Thread
import cv2


class LastFrameCollector:
    def __init__(self, video_path: str) -> None:
        self.video_path = video_path
        self.running = Value("b", True)

    def start(self, queue: Queue):
        self.process: Thread = Thread(
            target=self._start_collection,
            args=[queue, self.running],
            daemon=True,
            name="framecollector",
        )

    def stop(self):
        self.running.value = False

    def _start_collection(self, queue: Queue, running_flag):
        cam = cv2.VideoCapture(self.video_path, cv2.CAP_DSHOW)
        cam.set(cv2.CAP_PROP_AUTO_EXPOSURE, 3)
        cam.set(cv2.CAP_PROP_EXPOSURE, -3.0)

        cam.release()
        cam = cv2.VideoCapture(self.video_path, cv2.CAP_DSHOW)
        while running_flag.value:
            frame_running, frame = cam.read()
            if not frame_running:
                self.stop()
                break
            queue.put_nowait(frame)
        cam.release()
