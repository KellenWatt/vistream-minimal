
from .camera import Camera
import cv2 as cv
import numpy as np

from typing import Optional

def _detect_cameras(skip: int = 0, max_fail: int = 3) -> list[int]:
    failures = 0
    cam_id = skip
    ids = []
    while failures < max_fail:
        cam = cv.VideoCapture(cam_id)
        if cam is not None and cam.isOpened():
            ids.append(cam_id)
            failures = 0
        else:
            failures += 1
        cam.release()
        cam_id += 1
    print(ids)
    return ids


class CVCamera(Camera):
    cam: cv.VideoCapture

    possible_cameras = _detect_cameras()

    def __init__(self, source = None):
        """Create a new instance of a USB camera.

        `source` must be the valid video device number that can be accessed by OpenCV's
        `VideoCapture`. A limited, but significant number of devices are checked on startup
        and valid devices are listed in `USBCamera.possible_cameras`.

        If `source` is `None`, the first device from `USBCamera.possible_cameras` is used.
        """
        if source is not None and type(source) is not int:
            raise ValueError(f"device id must be an integer")
        
        if source is None:
            if len(USBCamera.possible_cameras) != 0:
                source = USBCamera.possible_cameras[0]
            else:
                raise ValueError("no known devices available. Cannot initialize camera")

        USBCamera.possible_cameras.remove(source)

        cam = cv.VideoCapture(source)
        cam.set(cv.CAP_PROP_FOURCC,cv.VideoWriter_fourcc(*"MJPG"))
        if not cam.isOpened():
            raise f"VideoCapture could not open source at '{source}'"
        self.cam = cam
        super().__init__()

    def source(self) -> cv.VideoCapture:
        return self.cam
    
    def frame_size(self) -> tuple[int, int]:
        return (int(self.cam.get(cv.CAP_PROP_FRAME_WIDTH)), int(self.cam.get(cv.CAP_PROP_FRAME_HEIGHT)))
    
    def _next_frame_(self) -> Optional[np.ndarray]:
        ok, frame = self.cam.read()
        if not ok:
            return None
        return frame
    
    def stop(self):
        super().stop()
        self.cam.release()

USBCamera = CVCamera
