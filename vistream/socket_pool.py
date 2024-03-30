from threading import Lock
import socket
from collections import deque

from typing import Optional

# This whole thing is a problem if the model shifts to being a process per stream group
class SocketPool:
    available_ports: deque[int]
    availability_lock: Lock
    port_range: range
    sockets: dict[int, socket.socket]


    def __init__(self, start: int, end: int):
        self.port_range = range(start, end+1)
        self.available_ports = deque(self.port_range)
        self.availability_lock = Lock()
        self.sockets = {}

    def allocate(self, port: Optional[int]) -> Optional[socket.socket]:
        with self.availability_lock:
            if len(self.available_ports) == 0 or port is not None and port not in self.available_ports:
                return None
            elif port in self.available_ports:
                self.available_ports.remove(port)
            else:  
                port = self.available_ports.popleft()
        
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.bind(("", port))

        self.sockets[port] = s
        print(f"port {port} allocated")

        return s

    def deallocate(self, port) -> bool:
        # technically not thread safe right here, but so vanishingly rare that we won't worry about it for now
        print(f"deallocating port {port}")
        if port not in self.sockets or port not in self.port_range:
            return False

        s = self.sockets[port]
        try:
            s.shutdown(socket.SHUT_RDWR)
            s.close()
        finally:
            with self.availability_lock:
                self.available_ports.append(port)
                del self.sockets[port]
            return True

        return True

    def collapse(self):
        opens = [p for p in self.sockets]
        for p in opens:
            self.deallocate(p)
