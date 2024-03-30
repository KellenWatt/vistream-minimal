import numpy as np
from threading import Thread, Lock, Event
from socket import socket
import time
import cv2 as cv


from .socket_buffer import BufferedSocket
from .socket_pool import SocketPool
from .camera import FrameSource
from .frame_limiter import FrameSequencer
from .message import format_data, format_frame
from .match_data import MatchData

from typing import Optional, Callable

import time


class MatchStream:
    source: FrameSource
    stream_size: Optional[tuple[int, int]]
    stream_rate: Optional[float]
    last_frame: float
    frame_delay: float

    frame_listener: Thread
    frame_connection_listener: socket
    frame_connections: list[socket]
    frame_connection_lock: Lock
    
    match_listener: Thread
    match_connection_listener: socket
    match_connections: list[socket]
    match_connection_lock: Lock

    matcher: Optional[Callable[[np.ndarray], list[MatchData]]]
    match_visualizer: Optional[Callable[[np.ndarray, list[MatchData]], np.ndarray]]
    match_worker: Thread

    terminate_call: Event

    @classmethod
    def create_socket_pool(cls, start, end):
        cls.socket_pool = SocketPool(start, end)

    def __init__(self, source: FrameSource, port: Optional[int] = None, stream_size: Optional[tuple[int, int]] = None, stream_rate: Optional[float] = None, compressed: bool = True):
        if not hasattr(MatchStream, "socket_pool"):
            raise ValueError("socket pool not initialized")
        self.source = FrameSequencer(source)
        self.stream_size = stream_size
        self.stream_rate = stream_rate
        self.compressed = compressed
        self.last_frame = 0
        if stream_rate is not None and stream_rate > 0:
            self.frame_delay = 1 / stream_rate
        else:
            self.frame_delay = 0

        self.terminate_call = Event()

        self.frame_connection_listener = MatchStream.socket_pool.allocate(port)
        self.frame_connection_listener.settimeout(1)
        if self.frame_connection_listener is None:
            raise ValueError("out of valid sockets")

        self.frame_connections = []
        self.frame_connection_lock = Lock()

        self.match_connection_listener = MatchStream.socket_pool.allocate(None if port is None else port+1)
        self.match_connection_listener.settimeout(1)
        if self.match_connection_listener is None:
            raise ValueError("out of valid sockets")

        self.match_connections = []
        self.match_connection_lock = Lock()

        def frame_listener():
            self.frame_connection_listener.listen()
            while not self.terminate_call.is_set():
                try:
                    sock, _addr = self.frame_connection_listener.accept()
                    with self.frame_connection_lock:
                        self.frame_connections.append(BufferedSocket(sock))
                except TimeoutError:
                    time.sleep(0.1)
                    pass

        self.frame_listener = Thread(target=frame_listener)

        def match_listener():
            self.match_connection_listener.listen()
            while not self.terminate_call.is_set():
                try:
                    sock, _addr = self.match_connection_listener.accept()
                    with self.match_connection_lock:
                        self.match_connections.append(BufferedSocket(sock))
                except TimeoutError:
                    time.sleep(0.1)
                    pass

        self.match_listener = Thread(target=match_listener)

        self.matcher = None
        self.match_visualizer = None
        
        def detect_send():
            while not self.terminate_call.is_set():
                if len(self.frame_connections) == 0 and len(self.match_connections) == 0:
                    time.sleep(0.1)
                    continue
                frame = self.source.get_frame()
                if frame is None:
                    time.sleep(0.05)
                    continue
                if self.matcher is not None and len(self.match_connections) > 0:
                    matches = self.matcher(frame)
                    if self.match_visualizer is not None:
                        frame = self.match_visualizer(frame, matches)
                   
                    msg = format_data(matches)
                    bads = []
                    for c in self.match_connections:
                        try:
                            c.write(msg, flush=True)
                        except:
                            c.close()
                            bads.append(c)
                    with self.match_connection_lock:
                        for c in bads:
                            self.match_connections.remove(c)
                
                if len(self.frame_connections) == 0:
                    continue
                if time.perf_counter() < self.last_frame + self.frame_delay:
                    continue
                self.last_frame = time.perf_counter()
                
                if self.stream_size is not None:
                    frame = cv.resize(frame, self.stream_size)
                msg = format_frame(frame, compressed = self.compressed)
                bads = []
                for c in self.frame_connections:
                    try:
                        c.write(msg, flush=True)
                    except:
                        c.close()
                        bads.append(c)
                with self.frame_connection_lock:
                    for c in bads:
                        self.frame_connections.remove(c)

        self.match_worker = Thread(target=detect_send)


    def start(self):
        if self.terminate_call.is_set():
            raise ValueError("cannot restart a terminated stream")
        self.frame_listener.start()
        self.match_listener.start()
        self.match_worker.start()

    def stop(self):
        if self.terminate_call.is_set():
            return
        self.terminate_call.set()
        self.frame_listener.join()
        self.match_listener.join()
        self.match_worker.join()
        type(self).socket_pool.deallocate(self.frame_connection_listener.getsockname()[1])
        type(self).socket_pool.deallocate(self.match_connection_listener.getsockname()[1])


    def set_matcher(self, matcher: Callable[[np.ndarray], list[MatchData]]):
        self.matcher = matcher

    def set_match_visualizer(self, viz: Callable[[np.ndarray, list[MatchData]], np.ndarray]):
        self.match_visualizer = viz
        
