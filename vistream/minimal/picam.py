import picamera2
import numpy as np

from typing import Optional

from .camera import Camera

class PiCamera(Camera):
    cam: picamera2.Picamera2
    _frame_size: tuple[int, int] 

    def __init__(self, size: tuple[int, int], mode: int = 0):
        """Creates a new instance of the Raspberry Pi camera connect to the CSI port
        By default the camera is launched into mode 0, which is usually, if not always, 
        the highest framerate. To determine the modes, you can run the following program.
        ```python
            from picamera2 import Picamera2
            from pprint import pprint
            cam = Picamera2()
            pprint(cam.sensormodes)
        ```

        Note that, since you can only have one Pi camera without external modules, attempting
        to instantiate this class more than once is undefined behaviour. It may work fine, 
        but don't count on it in general use.
        """
        cam = picamera2.Picamera2()
        mode = cam.sensor_modes[mode]
        config = cam.create_preview_configuration({"size": size, "format": "RGB888"},
                                 controls={"FrameDurationLimits": (100, 8333)},
                                 sensor={"output_size": mode["size"], "bit_depth": mode["bit_depth"]})

        cam.align_configuration(config)
        cam.configure(config)
        cam.start()
        self.cam = cam
        self._frame_size = config["main"]["size"]
        super().__init__()

    def source(self) -> picamera2.Picamera2:
        return self.cam

    def frame_size(self) -> tuple[int, int]:
        return self._frame_size

    def _next_frame_(self) -> Optional[np.ndarray]:
        return self.cam.capture_array()
