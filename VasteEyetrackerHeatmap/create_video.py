import glob
import re

import cv2
import numpy as np
import pandas as pd
from scipy.ndimage import gaussian_filter

# options
filter = 2
window = False # in seconds or false if no window

files = glob.glob('output*.mp4')
if len(files) != 0:
    file_indx = int(re.findall(r'\d+', files[-1])[0].split('.')[0]) + 1
else:
    file_indx = 0


df = pd.read_csv('video Metrics.tsv', sep='\t')
df = df.dropna(axis=1)

indexNames = df[ (df['FixationPointX'] < 0) | (df['FixationPointX'] > 1) | (df['FixationPointY'] < 0) | (df['FixationPointY'] > 1)].index
df.drop(indexNames , inplace=True)

df['X'] = df['FixationPointX'] * 1280
df['Y'] = df['FixationPointY'] * 720

df['X'] = np.array(df['X'].values).astype(np.uint16)
df['Y'] = np.array(df['Y'].values).astype(np.uint16)

xMin = df['X'].min()
xMax = df['X'].max()

yMin = df['Y'].min()
yMax = df['Y'].max()

last_timestamp = df.iloc[-1, df.columns.get_loc('Start')]

vidcap = cv2.VideoCapture('vid.mp4')
success, frame = vidcap.read()

if not success:
    print("Video not found")
    exit(1)

video_fps = vidcap.get(cv2.CAP_PROP_FPS),
total_frames = vidcap.get(cv2.CAP_PROP_FRAME_COUNT)
height = int(vidcap.get(cv2.CAP_PROP_FRAME_HEIGHT))
width = int(vidcap.get(cv2.CAP_PROP_FRAME_WIDTH))

writer = cv2.VideoWriter(f"output{file_indx}.mp4", cv2.VideoWriter_fourcc(*'mp4v'), video_fps[0], (int(width), int(height)))

if window:
    window_size = round(window * video_fps[0]) # window size in frames
    window *= 1000 # window in milliseconden

frame_time = (1 / video_fps[0]) * 1000 # milliseconden
count = 0


def make_heatmap(x, y):

    heatmap, xedges, yedges = np.histogram2d(x, y, bins=(width, height), range=[[xMin, xMax], [yMin, yMax]])
    heatmap *= 255
    heatmap = heatmap.astype(np.uint8).T
    heatmap = gaussian_filter(heatmap, sigma=filter)
    heatmap = cv2.applyColorMap(heatmap, cv2.COLORMAP_HSV)
    heatmap[np.where((heatmap==heatmap[700][0]).all(axis=2))] = [0, 0, 0]

    return heatmap

def process_image(frame, frameCount):

    window_start = 0

    if window:
        window_start = frameCount * frame_time - window

        if window_start < 0:
            window_start = 0

    window_end = frameCount * frame_time
        
    if last_timestamp < window_end:
        return None

    data = df.loc[(df['Start'] > window_start) & (df['Start'] < window_end) & (df['Participant'] == 'Jelle')]

    heatmap = make_heatmap(data['X'], data['Y'])

    print(f"Processing video {round((window_end / last_timestamp) * 100)}% done    ", end='\r')

    return cv2.addWeighted(frame, 1, heatmap, 1, 0)


while success:   

    try:
        result = process_image(frame, count) # process current frame

        if result is None:
            print("\n Done!")
            vidcap.release()
            writer.release()
            break

        writer.write(result) # write frame to output
        success, frame = vidcap.read()
        count += 1

    except KeyboardInterrupt:
        print("\n CTR-C, stopping...")
        vidcap.release()
        writer.release()