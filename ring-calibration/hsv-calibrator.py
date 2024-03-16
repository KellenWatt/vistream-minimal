from vistream.minimal.client import FrameStreamClient
import cv2 as cv
import atexit
import numpy as np
import io

from typing import Optional

import socket


from kivy.uix.widget import Widget
from kivy.app import App
from kivy.properties import ObjectProperty, StringProperty, NumericProperty, ReferenceListProperty, AliasProperty
from kivy.core.window import Window
from kivy.uix.image import Image
from kivy.graphics.texture import Texture
from kivy.event import EventDispatcher
from kivy.clock import Clock, ClockEvent
from kivy.uix.boxlayout import BoxLayout

class Stream(Image):
    frame_source: FrameStreamClient
    stream_event: Optional[ClockEvent]

    address = StringProperty(None)
    port = NumericProperty(None)

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
        self.stream_event = Clock.schedule_interval(lambda _dt: self.update(), 1/30)

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
            img = cv.flip(img, 0)
            img = cv.resize(img, self.size)
            #  img = cv.rotate(img, cv.ROTATE_90_COUNTERCLOCKWISE)
            bs = img.tobytes()

            tex = Texture.create(size=self.size)
            tex.blit_buffer(bs, colorfmt="bgr")
            self.texture = tex

    def shutdown(self):
        self.stop_stream()
        if self.frame_source is not None:
            self.frame_source.stop()

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
    
    

class SliderCalibrator(BoxLayout, EventDispatcher):
    hue = ObjectProperty(None)
    sat = ObjectProperty(None)
    val = ObjectProperty(None)

    host = StringProperty(None)
    port = NumericProperty(None)
   
    last_sent: bytearray

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.sender = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sender.settimeout(1)
        self.sender.connect((self.host, self.port))

        self.last_sent = bytearray(6)

    def update_calibrator(self):
        bs = bytearray(6)
        bs[0] = int(self.hue.low.value)
        bs[1] = int(self.hue.high.value)
        bs[2] = int(self.sat.low.value)
        bs[3] = int(self.sat.high.value)
        bs[4] = int(self.val.low.value)
        bs[5] = int(self.val.high.value)

        if self.last_sent != bs:
            print("new values")
            self.sender.send(bs)
            self.last_sent = bs



class HSVCalibratorApp(App):
    def build(self):
        return SliderCalibrator()


if __name__ == "__main__":
    HSVCalibratorApp().run()
