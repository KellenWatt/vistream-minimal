import numpy as np
from dataclasses import dataclass
from typing import Optional
import bitstring as bs
import math

import cv2 as cv

#  @dataclass
#  class Point:
#      x: int
#      y: int
#  
#      def offset(self, origin: "Point") -> "Point":
#          return Point(origin.x - self.x, origin.y - self.y)
#  
#  class BoundingBox:
#      x: int
#      y: int
#      width: int
#      height: int
#  
#      def __init__(self, x: int, y: int, w: int, h: int):
#          self.x = x
#          self.y = y
#          self.width = w
#          self.height = h
#  
#      @property
#      def top(self) -> int:
#          return self.y
#      @property
#      def left(self) -> int:
#          return self.x
#      @property
#      def bottom(self) -> int:
#          return self.y + self.height
#      @property
#      def right(self) -> int:
#          return self.x + self.width
#          
#      def top_left(self) -> Point:
#          return Point(self.left, self.top)
#          
#      def top_right(self) -> Point:
#          return Point(self.right, self.top)
#          
#      def bottom_left(self) -> Point:
#          return Point(self.left, self.bottom)
#          
#      def bottom_right(self) -> Point:
#          return Point(self.right, self.bottom)
#  
#      def center(self) -> Point:
#          x = (self.left + self.right) // 2
#          y = (self.top + self.bottom) // 2
#          return Point(x, y)
#  
#      @property
#      def major_axis(self) -> int:
#          return max(self.width, self.height)
#  
#      @property
#      def minor_axis(self) -> int:
#          return min(self.width, self.height)
#  
#  class MatchData:
#      complete: bool
#      box: BoundingBox
#      fiducial_id: Optional[int]
#  
#      def __init__(self, x: int, y: int, w: int, h: int, complete: bool, fiducial_id: Optional[int]):
#          self.complete = complete
#          self.box = BoundingBox(x, y, w, h)
#          self.fiducial_id = fiducial_id
#  
#      def is_complete(self) -> bool:
#          return self.complete
#  
#      def is_partial(self) -> bool:
#          return not self.complete
#  
#      def show(self, img, complete_match_color=(63,255,0), partial_match_color=(0,255,255), line_weight=3):
#          #img is assumed to be in BGR for the defaults, but it doesn't actually matter
#          if self.is_complete():
#              color = complete_match_color
#          else:
#              color = partial_match_color
#          b = self.box
#          return cv.rectangle(img, (b.left, b.top), (b.right, b.bottom), color, int(line_weight))
#  
#      def to_bytes(self) -> bytes:
#         out = bytearray()
#         fiducial_id = self.fiducial_id
#         if fiducial_id is None:
#             fiducial_id = 0
#         out.extend(bs.pack(["uintbe8", "uintbe16", "uintbe16", "uintbe16", "uintbe16", "uintbe8"],
#                            int(self.complete),
#                            self.box.x, self.box.y, self.box.width, self.box.height,
#                            fiducial_id).bytes)
#         return out
#  
#      @classmethod
#      def from_bytes(cls, b: bytes) -> "MatchData":
#          comp, x, y, w, h, fiducial_id = bs.Bits(bytes=b).unpack(["uintbe8", "uintbe16", "uintbe16", "uintbe16", "uintbe16", "uintbe8"])
#          if fiducial_id == 0:
#              fiducial_id = None
#          return cls(x, y, w, h, bool(comp), fiducial_id)
#  
#      @classmethod
#      def byte_length(cls) -> int:
#          return 10

@dataclass
class MatchContext:
    center: tuple[int, int]
    focal: tuple[int, int]
    item_size: tuple[float, float] # size in meters

@dataclass
class MatchData:
    x: float
    y: float
    z: float
    complete: bool
    fiducial_id: Optional[int]

    byte_layout = ["floatbe32", "floatbe32", "floatbe32", "uintbe8", "uintbe8"]

    @classmethod
    def from_2d(cls, x: int, y: int, match_size: tuple[int, int] | int, context: MatchContext, complete: bool = True, fiducial_id: Optional[int] = None) -> "MatchData":
        if type(match_size) is int:
            p_x = match_size
            p_y = match_size
        else:
            p_x = match_size[0]
            p_y = match_size[1]
        c_x = context.center[0]
        c_y = context.center[1]
        f_x = context.focal[0]
        f_y = context.focal[1]
        w_x = context.item_size[0]
        w_y = context.item_size[1]

        x3 = (x - c_x) * w_x / p_x
        y3 = (y - c_y) * w_y / p_y
        # we're going to assume square pixels, because the math gets weird (needs matrices) otherwise
        z3 = w_x * f_x / p_x 

        return cls(complete, x3, y3, z3, fiducial_id)
        


    def to_bytes(self) -> bytes:
        out = bytearray()
        fiducial_id = self.fiducial_id
        if fiducial_id is None:
            fiducial_id = 0
        out.extend(bs.pack(type(self).byte_layout,
                    self.x, self.y, self.z,
                    int(self.complete),
                    fiducial_id).tobytes())
        return out

    @classmethod
    def from_bytes(cls, b: bytes) -> "MatchData":
        x, y, z, comp, fid = bs.Bits(bytes=b).unpack(cls.byte_layout)
        if fid == 0:
            fid = None
        return cls(x, y, z, comp, fid)

    @classmethod
    def byte_length(cls) -> int:
        return 14

APRILTAG_CONTEXT = MatchContext(center = (307.72780607, 173.55162027),
                                 focal = (357.73227097, 356.44733473),
                                 item_size = (0.1651, 0.1651))

#  RING_CONTEXT = MatchContext(center = (),
#                              focal = (),
#                              item_size = (0.3556, 0.3556))
