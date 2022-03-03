import cv2
import numpy as np
import os

# target folder
folder = "frames/"

# use built in stitcher
stitcher = cv2.Stitcher_create()

# load images
filenames = os.listdir(folder)
images = []

for file in filenames:
    # get image
    img = cv2.imread(folder + file)
    images.append(img)


status, stitched = stitcher.stitch(images)

cv2.imshow("Stitched", stitched)
cv2.imwrite('panorama.png', stitched)
cv2.waitKey(0)