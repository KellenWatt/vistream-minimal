import numpy as np
import socket
from threading import Thread, Lock, Event

from typing import Optional


from .socket_buffer import BufferedSocket
from .message import parse_frame, parse_data, salvage_frame_stream, salvage_data_stream
from .match_data import MatchData

class FrameStreamClient:
    _latest_result: Optional[np.ndarray]
    listen_worker: Thread
    listener: BufferedSocket
    latest_lock: Lock

    terminate_call: Event

    def __init__(self, address: str, port: int):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(10)
        sock.connect((address, port))
        sock.settimeout(1)
        
        self.latest_lock = Lock()
        self.terminate_call = Event()
        self.listener = BufferedSocket(sock)
        def listen_up():
            try:
                while not self.terminate_call.is_set():
                    res = parse_frame(self.listener)
                    if res is not None:
                        self.latest_result = res
                    else:
                        if not salvage_frame_stream(self.listener):
                            raise "frame stream was corrupted and could not be salvaged"
            except OSError:
                self._latest_result = None
                return
                    

        self.listen_worker = Thread(target=listen_up)
        self._latest_result = None

    def start(self):
        if self.terminate_call.is_set():
            raise "cannot restart a terminated stream client"
        self.listen_worker.start()
                
    def stop(self):
        if self.terminate_call.is_set():
            return
        self.terminate_call.set()
        self.listener.sock.shutdown(socket.SHUT_RDWR)
        self.listener.sock.close()
        self.listen_worker.join()

    @property
    def latest_result(self) -> Optional[np.ndarray]:
        with self.latest_lock:
            return self._latest_result

    @latest_result.setter
    def latest_result(self, matches):
        with self.latest_lock:
            self._latest_result = matches

    def has_result(self) -> bool:
        return self._latest_result is not None

class MatchDataStreamClient:
    _latest_result: Optional[list[MatchData]]
    listen_worker: Thread
    listener: BufferedSocket
    latest_lock: Lock

    def __init__(self, address: str, port: int):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(10)
        sock.connect((address, port))
        sock.settimeout(5)

        self.latest_lock = Lock()
        self.terminate_call = Event()
        self.listener = BufferedSocket(sock)
        def listen_up():
            try:
                while not self.terminate_call.is_set(): 
                    res = parse_data(self.listener)
                    if res is not None:
                        self.latest_result = res
                    else: 
                        if not salvage_data_stream(self.listener):
                            raise "data stream was corrupted and could not be salvaged"
            except TimeoutError:
                self._latest_result = None
                return

        self.listen_worker = Thread(target=listen_up)
        self._latest_result = None

    def start(self):
        if self.terminate_call.is_set():
            raise "cannot restart a terminated stream client"
        self.listen_worker.start()

    def stop(self):
        self.terminate_call.set()

    @property
    def latest_result(self) -> Optional[list[MatchData]]:
        with self.latest_lock:
            return self._latest_result

    @latest_result.setter
    def latest_result(self, matches):
        with self.latest_lock:
            self._latest_result = matches

    def has_result(self) -> bool:
        return self._latest_result is not None
