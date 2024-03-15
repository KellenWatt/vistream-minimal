from vistream.minimal.client import FrameStreamClient, MatchDataStreamClient
import socket
import time
import cv2 as cv
import sys
import atexit
import numpy as np

source = FrameStreamClient("vision-2165.local", 1180)
print("source created")
source.start()

cv.namedWindow("test_frame", cv.WINDOW_NORMAL)

@atexit.register
def shutdown():
    print("Shutting down")
    source.stop()
    cv.destroyWindow("test_frame")

print("Awaiting frames")
while source.latest_result is None:
    time.sleep(0.1)

print("Frame recieved!")
    
start = time.perf_counter()
i=0
while cv.waitKey(5) != 27: # enter, escape, space
    res = source.latest_result
    
    cv.imshow("test_frame", res)
    i += 1

end = time.perf_counter()
print(f"{i/(end-start)}fps")


source.stop()
cv.destroyWindow("test_frame")
sys.exit(0)

#  source = MatchDataStreamClient("vision-2165.local", 1180)
#  print("source created")
#  source.start()
#  
#  @atexit.register
#  def shutdown():
#      print("Shutting down")
#      source.stop()
#      cv.destroyWindow("test_frame")
#  
#  
#  print("awaint matches")
#  while source.latest_result is None:
#      time.sleep(0.1)
#  
#  print("data recieved!")
#  
#  res = source.latest_result
#  
#  source.stop()
#  
#  print(len(res))
#  
