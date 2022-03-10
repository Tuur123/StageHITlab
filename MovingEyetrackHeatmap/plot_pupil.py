import pandas as pd
import numpy as np
import cv2
import matplotlib.pyplot as plt

df = pd.read_csv('gaze_positions.csv')

# Initiate SIFT detector
sift = cv2.SIFT_create()

FLANN_INDEX_KDTREE = 1
MIN_MATCH_COUNT = 10
index_params = dict(algorithm = FLANN_INDEX_KDTREE, trees = 5)
search_params = dict(checks = 50)

flann = cv2.FlannBasedMatcher(index_params, search_params)

vidcap = cv2.VideoCapture('world.mp4')
success, frame = vidcap.read()

video_fps = vidcap.get(cv2.CAP_PROP_FPS)
total_frames = vidcap.get(cv2.CAP_PROP_FRAME_COUNT)
height = int(vidcap.get(cv2.CAP_PROP_FRAME_HEIGHT))
width = int(vidcap.get(cv2.CAP_PROP_FRAME_WIDTH))

panorama = cv2.resize(cv2.imread('panorama.png'), (1400, height))
kp2, des2 = sift.detectAndCompute(panorama, None)

df['X'] = df['norm_pos_x'] * width
df['Y'] = height - df['norm_pos_y'] * height
df = df[['world_index', 'X', 'Y']]

df = df.astype({'world_index': int, 'X': int, 'Y': int})

writer = cv2.VideoWriter(f"output.mp4", cv2.VideoWriter_fourcc(*'mp4v'), video_fps, (panorama.shape[1] + width, height))
frame_idx = 0

while success:

    panorama_img = panorama.copy()

    # find the keypoints and descriptors with SIFT
    kp1, des1 = sift.detectAndCompute(frame, None)

    matches = flann.knnMatch(des1,des2,k=2)

    # store all the good matches as per Lowe's ratio test.
    good = []
    for m,n in matches:
        if m.distance < 0.7 * n.distance:
            good.append(m)

    if len(good)> MIN_MATCH_COUNT:
        src_pts = np.float32([ kp1[m.queryIdx].pt for m in good ]).reshape(-1,1,2)
        dst_pts = np.float32([ kp2[m.trainIdx].pt for m in good ]).reshape(-1,1,2)

        M, mask = cv2.findHomography(src_pts, dst_pts, cv2.RANSAC, 5.0)
        matchesMask = mask.ravel().tolist()

        h,w,c = frame.shape
        pts = np.float32([ [0,0],[0,h-1],[w-1,h-1],[w-1,0] ]).reshape(-1,1,2)
        dst = cv2.perspectiveTransform(pts, M)
        panorama_img = cv2.polylines(panorama_img, [np.int32(dst)], True, (0, 255, 0), 3, cv2.LINE_AA)

        idx, x, y = df.loc[(df['world_index'] == frame_idx)].mean()
        pan_x, pan_y = cv2.perspectiveTransform(np.float32([[x, y]]).reshape(-1,1,2), M)[0][0]

        cv2.circle(panorama_img, (int(pan_x), int(pan_y)), 5, (0, 0, 255), cv2.FILLED)
        try:
            cv2.circle(frame, (int(x), int(y)), 5, (0, 0, 255), cv2.FILLED)
        except:
            pass

        draw_params = dict(matchColor = (0,255,0), # draw matches in green color
                    singlePointColor = None,
                    matchesMask = matchesMask, # draw only inliers
                    flags = 2)

        result = cv2.drawMatches(frame, kp1, panorama_img, kp2, good, panorama_img, **draw_params)

        writer.write(np.concatenate((frame, panorama_img), axis=1))

    else:
        matchesMask = None

    success, frame = vidcap.read()
    frame_idx += 1

    print(f"\rDone {round((frame_idx / total_frames) * 100)}%", end='')

writer.release()
vidcap.release()