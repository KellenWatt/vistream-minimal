
from vistream.client import FrameStreamClient, MatchDataStreamClient
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
            size = [int(s) for s in self.size]
            img = cv.resize(img, size)
            bs = img.tobytes()

            tex = Texture.create(size=self.size)
            tex.blit_buffer(bs, colorfmt="bgr")
            tex.flip_vertical()
            self.texture = tex

    def shutdown(self):
        self.stop_stream()
        if self.frame_source is not None:
            self.frame_source.stop() 


class ATData(BoxLayout):
    coords = ObjectProperty(None)
    address = StringProperty(None)
    port = NumericProperty(None)
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        
        self.source = MatchDataStreamClient(self.address, self.port)
        self.source.start()
        #  Clock.schedule_once(lambda _: self.source.start())
        Clock.schedule_interval(lambda _: self.update(), 1/60)
        Window.bind(on_request_close=lambda _: self.source.stop())

    def update(self):
        if not self.source.has_result() or len(self.source.latest_result) == 0:
            self.coords.text = "No data yet!"
            return
        data = self.source.latest_result
        msg = ""
        for m in data:
            msg += f"ID: {m.fiducial_id}\nX: {m.x:.3f}\nY: {m.y:.3f}\nZ: {m.z:.3f}\n"
        self.coords.text = msg


class ATStream(App):
    def build(self):
        return ATData()

if __name__ == "__main__":
    ATStream().run()


