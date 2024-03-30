import numpy as np
import bitstring as bs
import cv2 as cv
import zlib
from .socket_buffer import BufferedSocket
from .match_data import MatchData

from typing import Optional, Any

#TODO Explore variable compression at lower framerates

FRAME_MAGIC_FLAG = bs.Bits(hex="99c3e3c5efe55837", length=64).bytes
def format_frame(frame: np.ndarray, compressed: bool = True) -> bytes:
    msg = bytearray(FRAME_MAGIC_FLAG)
    # This heavy compression leads to very low image quality, but also extremely small packet sizes
    if compressed:
        comp = cv.imencode(".jpg", frame, [cv.IMWRITE_JPEG_QUALITY, 9])[1].data # we're just going to assume it succeeds
    else:
        comp = cv.imencode(".png", frame)[1].data # we're just going to assume it succeeds
        #  comp = zlib.compress(frame.tobytes(), level = 4) # lower level to make faster, since we're streaming
    msg.extend(bs.pack(["uintbe32"], len(comp)).bytes)
    msg.extend(comp)

    return bytes(msg)

def parse_frame(sock: BufferedSocket) -> Optional[np.ndarray]:
    magic = sock.read(len(FRAME_MAGIC_FLAG))
    if magic is None or magic != FRAME_MAGIC_FLAG:
        return None

    shape = sock.read(4)
    if shape is None or len(shape) != 4:
        return None
    
    length = bs.Bits(bytes=shape).unpack(["uintbe32"])[0]
    #  width, height, length = bs.Bits(bytes=shape).unpack(["uintbe16", "uintbe16", "uintbe32"])

    frame_data = sock.read(length)
    if frame_data is None or len(frame_data) != length:
        return None
    
    #  frame_data = zlib.decompress(frame_data)
    frame_data = np.ndarray(length, buffer=frame_data, dtype=np.uint8)
    frame_data = cv.imdecode(frame_data, 1)

    #  return np.ndarray((height, width, 3), dtype="uint8", buffer=frame_data)
    return frame_data

def salvage_frame_stream(sock: BufferedSocket) -> bool:
    while sock.can_read():
        read = sock.peek(len(FRAME_MAGIC_FLAG))
        if read is None or len(read) < len(FRAME_MAGIC_FLAG):
            return False
        if read == FRAME_MAGIC_FLAG:
            return True
        sock.read(1)
    return False



DATA_MAGIC_FLAG = bs.Bits(hex="D5896268", length=32).bytes
def format_data(data: list[MatchData]) -> bytes:
    msg = bytearray(DATA_MAGIC_FLAG)
    msg.extend(bs.Bits(uintbe=len(data), length=16).bytes)
    for m in data:
        msg.extend(m.to_bytes())

    return bytes(msg)

def parse_data(sock: BufferedSocket) -> Optional[list[MatchData]]:
    magic = sock.read(len(DATA_MAGIC_FLAG))
    if magic is None or magic != DATA_MAGIC_FLAG:
        return None

    count_bytes = sock.read(2)
    if count_bytes is None or len(count_bytes) < 2:
        return None
    count: int = bs.Bits(bytes=count_bytes).unpack("uintbe16")[0]

    matches = []
    bytes_per = MatchData.byte_length()
    for _ in range(count):
        match_bytes = sock.read(bytes_per)
        if match_bytes is None or len(match_bytes) != bytes_per:
            return None
        matches.append(MatchData.from_bytes(match_bytes))

    return matches

def salvage_data_stream(sock: BufferedSocket) -> bool:
    print("trying to salvage stream")
    while sock.can_read():
        read = sock.peek(len(DATA_MAGIC_FLAG))
        if read is None or len(read) < len(DATA_MAGIC_FLAG):
            return False
        if read == DATA_MAGIC_FLAG:
            return True
        sock.read(1)
    return False


