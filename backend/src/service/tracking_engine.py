from typing import Dict, List
from model.tracking_model import MovingObject, TrackingMovingObject
import time


class TrackingEngine:
    MINIMUM_TRACKED = 1
    MINIMUM_SECOND_BEFORE_TRACK = 0.34
    MAXIMUM_SECOND_BEFORE_EXPIRE = 2

    pending_objects: Dict[str, TrackingMovingObject] = {}
    tracking_objects: Dict[str, TrackingMovingObject] = {}

    def update(self, objects: List[MovingObject]):
        current_second = time.time()

        self.remove_timeout_objects(current_second)
        self.remove_timeout_tracked_object(current_second)

        for moving_object in objects:
            id = moving_object.id
            corner = moving_object.corner

            object_pending = id in self.pending_objects
            object_tracking = id in self.tracking_objects

            if object_pending and not object_tracking:
                # Update pending object status
                pending_object = self.pending_objects[id]
                pending_object.detected_times += 1
                pending_object.corner = corner
                pending_object.last_update_second = current_second
            elif not object_pending and not object_tracking:
                # Add object into pending
                pending_object = TrackingMovingObject()
                pending_object.id = id
                pending_object.corner = corner
                pending_object.detected_times = 1
                pending_object.last_update_second = current_second
                self.pending_objects.update({id: pending_object})
            elif not object_pending and object_tracking:
                pending_object = self.tracking_objects[id]
                pending_object.detected_times += 1
                pending_object.corner = corner
                pending_object.last_update_second = current_second
        self.promote_object_to_tracking(current_second)

    def remove_timeout_objects(self, current_millis: float):
        object_id_delete = []
        for id, object in self.pending_objects.items():
            less_than_tracked = object.detected_times < self.MINIMUM_TRACKED
            more_than_tracked_time = (
                current_millis - object.last_update_second
            ) > self.MINIMUM_SECOND_BEFORE_TRACK
            if less_than_tracked and more_than_tracked_time:
                object_id_delete.append(id)

        for id in object_id_delete:
            self.pending_objects.pop(id)

    def remove_timeout_tracked_object(self, current_millis: float):
        object_id_delete = []
        for id, object in self.tracking_objects.items():
            more_than_tracked_time = (
                current_millis - object.last_update_second
            ) > self.MAXIMUM_SECOND_BEFORE_EXPIRE
            if more_than_tracked_time:
                object_id_delete.append(id)
        for id in object_id_delete:
            self.tracking_objects.pop(id)

    def promote_object_to_tracking(self, current_millis: float):
        object_id_to_promote = []
        for id, object in self.pending_objects.items():
            more_than_tracked = object.detected_times >= self.MINIMUM_TRACKED
            less_than_tracked_time = (
                current_millis - object.last_update_second
            ) <= self.MINIMUM_SECOND_BEFORE_TRACK
            if more_than_tracked and less_than_tracked_time:
                object_id_to_promote.append(id)
        for object_id in object_id_to_promote:
            self.tracking_objects.update({object_id: self.pending_objects[object_id]})
            self.pending_objects.pop(object_id)
