import os
os.environ["LIBCAMERA_LOG_LEVELS"] = "*:WARN"

import cv2 as cv
import time
import numpy as np
from collections import deque
from threading import Thread, Lock, Event


from typing import Any, Optional, Callable

class FrameSource:
    def get_frame(self) -> Optional[np.ndarray]:
        """Returns the current frame of the device, in the form of a `numpy.ndarray`.
        This method does not inherently guarantee unique frames per call, though some
        subclasses may provide this guarantee.

        The `Optional` annotation is intended to allow for non-blocking operations.
        However, blocking is assumed to be the default, and blocking operations should
        never return `None`.
        """
        raise NotImplementedError

    def source(self) -> Any:
        """Returns the raw, root frame source. This will most often be a class representing 
        some kind of camera, and does not guarantee any API.
        """
        raise NotImplementedError

    def frame_size(self) -> tuple[int, int]:
        """The size of the default frame returned, in pixels. Required for reconstructing 
        frame data on the client side
        """
        raise NotImplementedError

    def frame_id(self) -> int:
        """The id of the current frame. Generally assumed to increment for sequenctial frames, 
        but it's really only important that frames have unique ids over a reasonable period of time.
        """
        raise NotImplementedError

    def field_of_view(self) -> tuple[float, float]:
        """The horizontal and vertical field-of-views of the root frame source, respectively."""
        raise NotImplementedError

class Camera(FrameSource):
    frame_grabber: Thread
    frame_lock: Lock
    stop_capture: Event
    current_frame: np.ndarray
    _frameid: int

    def __init__(self):
        self.frame_lock = Lock()
        self.stop_capture = Event()
        # Only one thread should ever modify this, so no need for a mutex
        self._frameid = 0
        self.current_frame = None

        def _grab_frame():
            while not self.stop_capture.is_set():
                frame = self._next_frame_()
                if frame is None:
                    continue
                with self.frame_lock:
                    self.current_frame = frame
                self._frameid += 1
        self._frame_grabber_f = _grab_frame
        self.frame_grabber = Thread(target=self._frame_grabber_f)
        self.frame_grabber.start()
       
    def is_capturing(self) -> bool:
        return self.frame_grabber is not None and self.frame_grabber.is_alive()

    def stop(self):
        if self.stop_capture.is_set():
            return
        self.stop_capture.set()
        self.frame_grabber.join()

    def get_frame(self) -> np.ndarray:
        """Returns the most recent frame captured by the camera. This is non-blocking 
        (technically. There is a mutex involved), and can result in the same image 
        between calls. For semi-guaranteed sequential frames, prefer any of the 
        frame limiter/sequencer classes.

        Frame data is returned as a `numpy.ndarray` with depth 3 in BGR format
        """
        with self.frame_lock:
            # shouldn't take very long to copy, but better safe than sorry
            res = self.current_frame
        return res

    def _next_frame_(self) -> Optional[np.ndarray]:
        raise NotImplementedError

    def source(self) -> Any:
        raise NotImplementedError

    def frame_size(self) -> tuple[int, int]:
        raise NotImplementedError

    def frame_id(self) -> int:
        return self._frameid


Layer = Callable[[np.ndarray], np.ndarray]

class ProcessedCamera(FrameSource):
    _source: FrameSource

    frame_grabber: Thread
    frame_lock: Lock
    current_frame: np.ndarray
    _frame_id: int

    layers: list[Layer]

    def __init__(self, source):
        self._source = source
        self.frame_lock = Lock()
        self.stop_capture = Event()
        # Only one thread should ever modify this, so no need for a mutex
        self._frame_id = 0

        self.layers = []
        self.current_frame = None

        def _grab_frame():
            while not self.stop_capture.is_set():
                if self._frame_id == self._source.frame_id():
                    continue
                frame = self._source.get_frame()
                self._frame_id = self._source.frame_id()
                if frame is None:
                    continue
                for layer in self.layers:
                    frame = layer(frame)
                with self.frame_lock:
                    self.current_frame = frame
        self.frame_grabber = Thread(target=_grab_frame)
        self.frame_grabber.start()
       
    def stop(self):
        if self.stop_capture.is_set():
            return
        self.stop_capture.set()
        self.frame_grabber.join()
        self._source.stop()

    def is_capturing(self) -> bool:
        return self.frame_grabber is not None and self.frame_grabber.is_alive()

    def get_frame(self) -> np.ndarray:
        """Returns the most recent frame captured by the camera. This is non-blocking 
        (technically. There is a mutex involved), and can result in the same image 
        between calls. For semi-guaranteed sequential frames, prefer any of the 
        frame limiter/sequencer classes.

        Frame data is returned as a `numpy.ndarray` with depth 3 in BGR format
        """
        with self.frame_lock:
            # shouldn't take very long to copy, but better safe than sorry
            res = self.current_frame
        return res

    def add_layer(self, layer: Layer):
        self.layers.append(layer)

    def source(self) -> Any:
        return self._source.source()

    def frame_size(self) -> tuple[int, int]:
        return self._source.frame_size()
    
    def frame_id(self) -> int:
        return self._frame_id
