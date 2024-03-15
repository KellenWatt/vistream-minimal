from vistream.minimal.client import FrameStreamClient
import cv2 as cv
import atexit
import numpy as np
import io

from typing import Optional


from kivy.uix.widget import Widget
from kivy.app import App
from kivy.properties import ObjectProperty, StringProperty, NumericProperty
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
            img = cv.flip(img, 0)
            img = cv.resize(img, self.size[::-1])
            img = cv.rotate(img, cv.ROTATE_90_COUNTERCLOCKWISE)
            bs = img.tobytes()

            tex = Texture.create(size=self.size)
            tex.flip_horizontal()
            tex.flip_vertical()
            tex.blit_buffer(bs, colorfmt="bgr")
            self.texture = tex

    def shutdown(self):
        self.stop_stream()
        if self.frame_source is not None:
            self.frame_source.stop()


class StreamControl(Widget):
    button_label = StringProperty("Start")
    button_color = StringProperty("green")
    stream = ObjectProperty(None)

    def start_stream(self):
        self.stream.start_stream()
        self.button_label = "Pause"
        self.button_color = "red"

    def stop_stream(self):
        self.stream.stop_stream()
        self.button_label = "Continue"
        self.button_color = "green"

    def toggle_stream(self):
        if self.stream.is_enabled():
            self.stop_stream()
        else:
            self.start_stream()

class StreamBox(BoxLayout):
    stream_a = ObjectProperty(None)
    stream_b = ObjectProperty(None)
    
    def shutdown(self):
        stream_a.shutdown()
        stream_b.shutdown()

class StreamingApp(App):
    def build(self):
        self.capture = StreamBox()
        return self.capture

    def on_request_close(self, *args):
        self.capture.shutdown()

if __name__ == "__main__":
    StreamingApp().run()
