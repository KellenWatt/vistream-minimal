from vistream.minimal.client import FrameStreamClient
import cv2 as cv
import atexit
import numpy as np
import io

from typing import Optional

import socket
from kivy.config import Config

Config.set("graphics", "width", "960")


from kivy.uix.widget import Widget
from kivy.app import App
from kivy.properties import ObjectProperty, StringProperty, NumericProperty, ReferenceListProperty, AliasProperty
from kivy.core.window import Window
from kivy.uix.image import Image
from kivy.graphics.texture import Texture
from kivy.event import EventDispatcher
from kivy.clock import Clock, ClockEvent
from kivy.uix.boxlayout import BoxLayout


class RangeSliderGroup(BoxLayout):
    low = ObjectProperty(None)
    high = ObjectProperty(None)

    name = StringProperty("")
    label = StringProperty("")

    def on_name(self, _inst, value):
        self.update_label()

    def update_label(self):
        self.label = f"{self.name}\n[{int(self.low.value)} - {int(self.high.value)}]"

    def bound_low(self):
        if self.low.value > self.high.value:
            self.low.value = self.high.value
        self.update_label()

    def bound_high(self):
        if self.high.value < self.low.value:
            self.high.value = self.low.value
        self.update_label()


class Stream(Image):
    frame_source: FrameStreamClient
    stream_event: Optional[ClockEvent]

    address = StringProperty(None)
    port = NumericProperty(None)

    processing_layer = ObjectProperty(None)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.frame_source = None
        Window.bind(on_request_close=lambda _junk: self.shutdown())
        self.stream_event = None
        Clock.schedule_once(lambda _evt: self.start_stream(), 0.3)

    def start_stream(self):
        if self.frame_source is None:
            self.frame_source = FrameStreamClient(self.address, self.port)
            self.frame_source.start()
        if self.stream_event is not None:
            return
        self.stream_event = Clock.schedule_interval(lambda _dt: self.update(), 1/60)

    def stop_stream(self):
        if self.stream_event is None:
            return
        self.stream_event.cancel()
        self.stream_event = None

    def is_enabled(self) -> bool:
        return self.stream_event is not None

    def update(self):
        if self.frame_source.latest_result is not None:
            img = self.frame_source.latest_result
            if self.processing_layer is not None:
                img = self.processing_layer(img)
            #  img = cv.flip(img, 0)
            img = cv.resize(img, self.size)
            #  img = cv.rotate(img, cv.ROTATE_90_COUNTERCLOCKWISE)
            bs = img.tobytes()

            tex = Texture.create(size=self.size)
            tex.blit_buffer(bs, colorfmt="bgr")
            tex.flip_vertical()
            self.texture = tex

    def shutdown(self):
        self.stop_stream()
        if self.frame_source is not None:
            self.frame_source.stop() 
    

class SliderCalibrator(BoxLayout, EventDispatcher):
    hue = ObjectProperty(None)
    sat = ObjectProperty(None)
    val = ObjectProperty(None)

    host = StringProperty(None)
    port = NumericProperty(None)
  
    raw = ObjectProperty(None)
    mask = ObjectProperty(None)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        #  self.sender = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        #  self.sender.settimeout(1)
        #  self.sender.connect((self.host, self.port))

        #  self.last_sent = bytearray(6)

    def update_calibrator(self):
        bs = bytearray(6)
        #  bs[0] = int(self.hue.low.value)
        #  bs[1] = int(self.hue.high.value)
        #  bs[2] = int(self.sat.low.value)
        #  bs[3] = int(self.sat.high.value)
        #  bs[4] = int(self.val.low.value)
        #  bs[5] = int(self.val.high.value)

        #  if self.last_sent != bs:
        #      print("new values")
        #      self.sender.send(bs)
        #      self.last_sent = bs

    @property
    def low(self) -> np.ndarray:
        return np.array([self.hue.low.value, self.sat.low.value, self.val.low.value], dtype="uint8")
    
    @property
    def high(self) -> np.ndarray:
        return np.array([self.hue.high.value, self.sat.high.value, self.val.high.value], dtype="uint8")

    def update_mask(self):
        pix = self.raw.texture.pixels
        img = np.frombuffer(pix, dtype="uint8").reshape(*self.raw.size[::-1], 4)
        img = cv.cvtColor(img, cv.COLOR_RGBA2RGB)
        img_hsv = cv.cvtColor(img, cv.COLOR_RGB2HSV_FULL)
        mask = cv.inRange(img_hsv, self.low, self.high)
        mask = cv.resize(mask, (1280, 720))

        tex = Texture.create(size=self.mask.size)
        tex.blit_buffer(cv.cvtColor(mask, cv.COLOR_GRAY2RGB).tobytes(), colorfmt="rgb")
        tex.flip_vertical()
        self.mask.texture = tex


    #  def match_rings(frame: np.ndarray) -> list[MatchData]:
    #      img_hsv = cv.cvtColor(frame, cv.COLOR_BGR2HSV_FULL)
    #      mask = cv.inRange(img_hsv, np.array([7, 65, 205]), np.array([35, 255, 255]))
    #      contours, hierarchy = cv.findContours(mask, cv.RETR_EXTERNAL, cv.CHAIN_APPROX_SIMPLE)
    #      out = cv.cvtColor(mask, cv.COLOR_GRAY2RGB)
    #  
    #      matches = []
    #  
    #      for c in contours:
    #          perimeter = cv.arcLength(c, True)
    #          if perimeter == 0:
    #              continue
    #  
    #          area = cv.contourArea(c)
    #          roundness = 4 * math.pi * area/(perimeter * perimeter)
    #  
    #          full_match = roundness > 0.6
    #          x,y,w,h = cv.boundingRect(c)
    #  
    #          if w > 0.06 * frame.shape[1]  and h > 0.03 * frame.shape[0]:
    #              match = MatchData(x, y, w, h, full_match, None)
    #              matches.append(match)
    #  
    #      return matches
    #  


class HSVCalibratorApp(App):
    def build(self):
        return SliderCalibrator()


if __name__ == "__main__":
    HSVCalibratorApp().run()
