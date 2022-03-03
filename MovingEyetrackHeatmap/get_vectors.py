import numpy as np
import cv2

cap = cv2.VideoCapture('world.mp4')

ret, frame1 = cap.read()
prvs = cv2.cvtColor(frame1, cv2.COLOR_BGR2GRAY)
prvs = np.resize(prvs, (256, 256))

length = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
vectors = []

count = 0

while True:

    ret, frame2 = cap.read()

    if not ret:
        print('\nNo frames grabbed!')
        break

    next = cv2.cvtColor(frame2, cv2.COLOR_BGR2GRAY)
    next = cv2.resize(next, (256, 256))
    flow = cv2.calcOpticalFlowFarneback(prvs, next, None, 0.5, 3, 15, 3, 5, 1.2, 0)
    prvs = next

    flow = flow.astype(np.uint16)
    vectors.append(flow)
    count += 1

    print(f"\r{round((count / length) * 100)}% Done", end='', flush=True)

np.save('vectors.npy', vectors)