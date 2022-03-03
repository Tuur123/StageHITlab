import cv2
import numpy as np
import os
import shutil

# rescale the images
def rescale(img):
    scale = 0.5
    h,w = img.shape[:2]
    h = int(h*scale)
    w = int(w*scale)
    return cv2.resize(img, (w,h))

# delete and create directory
folder = "frames/"
if os.path.isdir(folder):
    shutil.rmtree(folder)
os.mkdir(folder)

# open vidcap
cap = cv2.VideoCapture("world.mp4") # your video here
counter = 0

length = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
print(f"Total frames in file: {length}")


# make an orb feature detector and a brute force matcher
orb = cv2.ORB_create()
bf = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=False)

# store the first frame
_, last = cap.read()
last = rescale(last)
cv2.imwrite(folder + str(counter).zfill(5) + ".png", last)

# get the first frame's stuff
kp1, des1 = orb.detectAndCompute(last, None)

# cutoff, the minimum number of keypoints
cutoff = 50

# count number of frames
prev = None
while True:

    # get frame
    ret, frame = cap.read()
    if not ret:
        break

    # resize
    frame = rescale(frame)

    # count keypoints
    kp2, des2 = orb.detectAndCompute(frame, None)

    # match
    matches = bf.knnMatch(des1, des2, k=2)

    # lowe's ratio
    good = []
    for m, n in matches:
        if m.distance < 0.5 * n.distance:
            good.append(m)

    if len(good) < cutoff:
        # swap and save
        counter += 1
        last = frame
        kp1 = kp2
        des1 = des2
        cv2.imwrite(folder + str(counter).zfill(5) + ".png", last)
        print("\rNew Frame: " + str(counter), end='', flush=True)

    prev = frame

# also save last frame
counter += 1
cv2.imwrite(folder + str(counter).zfill(5) + ".png", prev)

# check number of saved frames
print("\nCounter: " + str(counter))