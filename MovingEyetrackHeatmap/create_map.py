import cv2
import numpy as np
import pandas as pd

df = pd.read_csv('gaze_positions.csv')

vidcap = cv2.VideoCapture('world.mp4')
success, frame = vidcap.read()

video_fps = vidcap.get(cv2.CAP_PROP_FPS)
total_frames = vidcap.get(cv2.CAP_PROP_FRAME_COUNT)
height = int(vidcap.get(cv2.CAP_PROP_FRAME_HEIGHT))
width = int(vidcap.get(cv2.CAP_PROP_FRAME_WIDTH))

df['X'] = df['norm_pos_x'] * width
df['Y'] = height - df['norm_pos_y'] * height
df = df[['world_index', 'X', 'Y']]

df = df.loc[df['Y'] > 0]

df = df.astype({'world_index': int, 'X': int, 'Y': int})

cv2.findHomography