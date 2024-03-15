from kivy.uix.widget import Widget
from kivy.app import App
from kivy.properties import StringProperty, NumericProperty, ObjectProperty, BooleanProperty
from kivy.uix.image import Image
from kivy.graphics.texture import Texture
from kivy.clock import Clock, ClockEvent
from kivy.core.image import Image as CoreImage

import cv2 as cv
import numpy as np

from typing import Optional

from glob import glob
import os
import copy


def get_next_filename(prefix: str = "img") -> str:
    files = glob(f"images/{prefix}*.png")
    return f"{prefix}{len(files):03d}.png"

CHECKERBOARD = (8, 6)
criteria = (cv.TERM_CRITERIA_EPS + cv.TERM_CRITERIA_MAX_ITER, 30, 0.001)
def show_checkerboard(img: np.ndarray) -> np.ndarray:
    gray = cv.cvtColor(img, cv.COLOR_BGR2GRAY)

    ret, corners = cv.findChessboardCorners(gray, CHECKERBOARD, cv.CALIB_CB_ADAPTIVE_THRESH + cv.CALIB_CB_FAST_CHECK + cv.CALIB_CB_NORMALIZE_IMAGE)

    if not ret:
        return img

   
    corners2 = cv.cornerSubPix(gray, corners, (11,11),(-1,-1), criteria)
    cpy = cv.drawChessboardCorners(copy.deepcopy(img), CHECKERBOARD, corners2, ret)

    return cpy

DIM=(640, 360)
K=np.array([[357.73227097100624, 0.0, 307.7278060660069], [0.0, 356.44733473350254, 173.55162026508373], [0.0, 0.0, 1.0]])
D=np.array([[-0.09720157189831408], [-0.005837301167328796], [-0.007848844103543036], [0.0028272917117362056]])
def undistort(img: np.ndarray) -> np.ndarray:
    h,w = img.shape[:2]
    map1, map2 = cv.fisheye.initUndistortRectifyMap(K, D, np.eye(3), K, DIM, cv.CV_16SC2)
    undistorted_img = cv.remap(img, map1, map2, interpolation=cv.INTER_LINEAR, borderMode=cv.BORDER_CONSTANT)
    return undistorted_img

class CaptureCamera(Widget):
    playback = StringProperty("Pause")
    live_feed = ObjectProperty(None)
    checker = ObjectProperty(None)
    play = BooleanProperty(True)

    cam: cv.VideoCapture
    latest_frame = ObjectProperty(None, force_dispatch=True)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.cam = cv.VideoCapture(0)
        self.dims = (640, 360)
        Clock.schedule_interval(self.update_frame , 1/30)

    def update_frame(self, _evt):
        if not self.play:
            return
        ok, frame = self.cam.read()
        if not ok:
            return
        frame = cv.resize(frame, self.dims)
        self.latest_frame = frame

    def on_latest_frame(self, _inst, value):
        if value is None:
            return
        self.show_frame(value, self.live_feed)
        self.show_frame(undistort(value), self.checker) 

    def show_frame(self, img: np.ndarray, image: Image):
        bs = img.tobytes()
        tex = Texture.create(size = self.dims)
        tex.blit_buffer(bs, colorfmt="bgr")
        tex.flip_vertical()
        image.texture = tex

    def pause_play(self):
        if self.play:
            self.play = False
            self.playback = "Play"
        else:
            self.play = True
            self.playback = "Pause"

    def capture(self):
        #  tex = self.cam.texture
        if not os.path.isdir("images"):
            os.mkdir("images")
        self.live_feed.texture.save(f"images/{get_next_filename('img')}", flipped=False)

    def capture_proc(self):
        if not os.path.isdir("images"):
            os.mkdir("images")
        self.checker.texture.save(f"images/{get_next_filename('proc')}", flipped=False)


class CalibratorApp(App):
    def build(self):
        return CaptureCamera()


if __name__ == "__main__":
    CalibratorApp().run()
