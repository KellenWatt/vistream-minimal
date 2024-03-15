from vistream.minimal.client import FrameStreamClient
import cv2 as cv
import time
import sys
import atexit
import numpy as np
import copy

CHECKERBOARD = (7, 7)
criteria = (cv.TERM_CRITERIA_EPS + cv.TERM_CRITERIA_MAX_ITER, 30, 0.001)

def show_checkerboard(img: np.ndarray) -> np.ndarray:
    cpy = copy.deepcopy(img)
    gray = cv.cvtColor(cpy, cv.COLOR_BGR2GRAY)

    ret, corners = cv.findChessboardCorners(gray, CHECKERBOARD, cv.CALIB_CB_ADAPTIVE_THRESH + cv.CALIB_CB_FAST_CHECK + cv.CALIB_CB_NORMALIZE_IMAGE)

    if not ret:
        return img

    
    corners2 = cv.cornerSubPix(gray, corners, (11,11),(-1,-1), criteria)
    cpy = cv.drawChessboardCorners(cpy, CHECKERBOARD, corners2, ret)

    return cpy


cam = cv.VideoCapture(0)
cam.set(cv.CAP_PROP_FOURCC,cv.VideoWriter_fourcc(*"MJPG"))


#  source = FrameStreamClient("vision-2165.local", 1180)
#  source.start()
#  win_name = "calibration_frame"
#  cv.namedWindow(win_name)
#  
#  @atexit.register
#  def shutdown():
#      print("Shutting down")
#      source.stop()
#      cv.destroyWindow(win_name)

#  print("Awaiting frames")
#  while source.latest_result is None:
#      time.sleep(0.1)
#  
#  print("Frame recieved!")

images_saved = 0
while True:
    key = cv.waitKey(30)
    ok, res = cam.read()
    if not ok:
        continue
    cv.imshow("calibration_frame", show_checkerboard(res))
    if key == 27:
        break
    if key == 32:
        path = f"calibration_images/{images_saved}.png"
        cv.imwrite(path, res)
        print(f"image saved to {path}")
        images_saved += 1

source.stop()
cv.destroyWindow(win_name)
sys.exit(0)


