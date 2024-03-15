from typing import Optional
import cv2 as cv
import numpy as np

from vistream.minimal.message import *
from vistream.minimal.match_data import MatchData

class BufferedSocket:
    data: bytearray

    def __init__(self, buffer: bytes = bytes()):
        self.data = bytearray(buffer)

    def can_read(self) -> bool:
        return len(self.data) != 0

    def write(self, bs: bytes, flush: bool = False) -> bool:
        self.data.extend(buffer)
        return True

    def peek(self, n: int) -> Optional[bytes]:
        return bytes(self.data[:n])

    def read(self, n: int) -> Optional[bytes]:
        if n > len(self.data):
            return None
        res = self.data[:n]
        self.data = self.data[n:]
        return bytes(res)


def random_match() -> MatchData:
    fid = np.random.randint(256)
    if fid == 0:
        fid = None
    return MatchData(*np.random.randint(5000, size=4), bool(np.random.randint(2)), fid)

def match_equal(m, n) -> bool:
    return m.box.x == n.box.x and\
        m.box.y == n.box.y and\
        m.box.width == n.box.width and\
        m.box.height == n.box.height and\
        m.complete == n.complete and\
        m.fiducial_id == n.fiducial_id


image = cv.imread("demo.jpg")

msg = format_frame(image)
buf = BufferedSocket(msg)
print(len(buf.data))
out_image = parse_frame(buf)
assert out_image is not None
assert np.array_equal(image, out_image)
print("format_frame and parse_frame are inverse operations")

msg = format_frame(image)
for i in range(100):
    junk_msg = bytearray(np.random.bytes(np.random.randint(1000)))
    junk_msg.extend(msg)
    buf = BufferedSocket(junk_msg)
    assert salvage_frame_stream(buf)
    print(f"\r{i+1}% complete", end="")
print("\nsalvage_frame_stream salvages stream from random data")


for i in range(1000):
    match = random_match()
    msg = format_data([match])
    buf = BufferedSocket(msg)
    out_match = parse_data(buf)
    assert len(out_match) == 1
    assert match_equal(match, out_match[0])
    print(f"\r{(i+1) / 10}% complete", end="")
print("\nsingle matching equal")

for i in range(100):
    match_count = np.random.randint(30)
    matches = [random_match() for _ in range(match_count)]
    msg = format_data(matches)
    buf = BufferedSocket(msg)
    out_match = parse_data(buf)
    assert len(out_match) == match_count
    assert all(match_equal(matches[i], out_match[i]) for i in range(match_count))
    print(f"\r{(i+1)}% complete", end="")
print("\nplural matches transmit")

for i in range(100):
    match_count = np.random.randint(30)
    matches = [random_match() for _ in range(match_count)]
    msg = format_data(matches)
    junk_msg = bytearray(np.random.bytes(np.random.randint(1000)))
    junk_msg.extend(msg)
    buf = BufferedSocket(junk_msg)
    assert salvage_data_stream(buf)
    print(f"\r{i+1}% complete", end="")

print("\nsalvage_data_stream salvages stream from random data")


