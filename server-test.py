#!/bin/env python3

from vistream.cvcam import USBCamera
from vistream.camera import ProcessedCamera
from vistream.server import MatchStream
from vistream.match_data import MatchData


import atexit
import signal
import sys
import time
import cv2 as cv
import numpy as np


MatchStream.create_socket_pool(1180, 1190)
cam = USBCamera(0)
#  cam = ProcessedCamera(cam)
#  cam.add_layer(lambda img: cv.resize(img, (320, 180)))

stream = MatchStream(cam, 1180, stream_size=(320,240))

#  def random_match(n: int) -> list[MatchData]:
#      out = []
#      for _ in range(np.random.randint(n)+1):
#          fid = np.random.randint(256)
#          if fid == 0:
#              fid = None
#          m = MatchData(*np.random.randint(5000, size=4), bool(np.random.randint(2)), fid)
#          out.append(m)
#      return out
#  
#  def matcher(_frame: np.ndarray) -> list[MatchData]:
#      return random_match(10)
#  
#  stream.set_matcher(matcher)


@atexit.register
def shutdown():
    stream.stop()
    cam.stop()
    print("### shutting down ###")
    if hasattr(MatchStream, "socket_pool"):
        MatchStream.socket_pool.collapse()

def interrupt(_sig, _frame):
    shutdown()
    sys.exit(0)

signal.signal(signal.SIGINT, interrupt)


stream.start()
print("Stream starting")
while True:
    time.sleep(1000)

