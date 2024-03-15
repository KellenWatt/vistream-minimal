import numpy as np
from dataclasses import dataclass
from typing import Optional
import bitstring as bs
import math

import cv2 as cv

@dataclass
class Point:
    x: int
    y: int

    def offset(self, origin: "Point") -> "Point":
        return Point(origin.x - self.x, origin.y - self.y)

class BoundingBox:
    x: int
    y: int
    width: int
    height: int

    def __init__(self, x: int, y: int, w: int, h: int):
        self.x = x
        self.y = y
        self.width = w
        self.height = h

    @property
    def top(self) -> int:
        return self.y
    @property
    def left(self) -> int:
        return self.x
    @property
    def bottom(self) -> int:
        return self.y + self.height
    @property
    def right(self) -> int:
        return self.x + self.width
        
    def top_left(self) -> Point:
        return Point(self.left, self.top)
        
    def top_right(self) -> Point:
        return Point(self.right, self.top)
        
    def bottom_left(self) -> Point:
        return Point(self.left, self.bottom)
        
    def bottom_right(self) -> Point:
        return Point(self.right, self.bottom)

    def center(self) -> Point:
        x = (self.left + self.right) // 2
        y = (self.top + self.bottom) // 2
        return Point(x, y)

    @property
    def major_axis(self) -> int:
        return max(self.width, self.height)

    @property
    def minor_axis(self) -> int:
        return min(self.width, self.height)

class MatchData:
    complete: bool
    box: BoundingBox
    fiducial_id: Optional[int]

    def __init__(self, x: int, y: int, w: int, h: int, complete: bool, fiducial_id: Optional[int]):
        self.complete = complete
        self.box = BoundingBox(x, y, w, h)
        self.fiducial_id = fiducial_id

    def is_complete(self) -> bool:
        return self.complete

    def is_partial(self) -> bool:
        return not self.complete

    def show(self, img, complete_match_color=(63,255,0), partial_match_color=(0,255,255), line_weight=3):
        #img is assumed to be in BGR for the defaults, but it doesn't actually matter
        if self.is_complete():
            color = complete_match_color
        else:
            color = partial_match_color
        b = self.box
        return cv.rectangle(img, (b.left, b.top), (b.right, b.bottom), color, int(line_weight))

    def to_bytes(self) -> bytes:
       out = bytearray()
       fiducial_id = self.fiducial_id
       if fiducial_id is None:
           fiducial_id = 0
       out.extend(bs.pack(["uintbe8", "uintbe16", "uintbe16", "uintbe16", "uintbe16", "uintbe8"],
                          int(self.complete),
                          self.box.x, self.box.y, self.box.width, self.box.height,
                          fiducial_id).bytes)
       return out

    @classmethod
    def from_bytes(cls, b: bytes) -> "MatchData":
        comp, x, y, w, h, fiducial_id = bs.Bits(bytes=b).unpack(["uintbe8", "uintbe16", "uintbe16", "uintbe16", "uintbe16", "uintbe8"])
        if fiducial_id == 0:
            fiducial_id = None
        return cls(x, y, w, h, bool(comp), fiducial_id)

    @classmethod
    def byte_length(cls) -> int:
        return 10


