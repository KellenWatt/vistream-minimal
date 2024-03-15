
import cv2
import numpy as np
import sys
DIM=(640, 360)
K=np.array([[357.73227097100624, 0.0, 307.7278060660069], [0.0, 356.44733473350254, 173.55162026508373], [0.0, 0.0, 1.0]])
D=np.array([[-0.09720157189831408], [-0.005837301167328796], [-0.007848844103543036], [0.0028272917117362056]])

def undistort(img_path):
    img = cv2.imread(img_path)
    h,w = img.shape[:2]
    map1, map2 = cv2.fisheye.initUndistortRectifyMap(K, D, np.eye(3), K, DIM, cv2.CV_16SC2)
    undistorted_img = cv2.remap(img, map1, map2, interpolation=cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT)
    cv2.imshow("undistorted", undistorted_img)
    cv2.waitKey(0)
    cv2.destroyAllWindows()
if __name__ == '__main__':
    for p in sys.argv[1:]:
        undistort(p)
    