import cv2
import numpy as np
import pandas as pd
from scipy.ndimage import gaussian_filter

df = pd.read_csv('video Metrics.tsv', sep='\t')

window = 3 # in seconds

vidcap = cv2.VideoCapture('vid.mp4')
success, frame = vidcap.read()

if not success:
    print("Video not found")
    exit(1)

video_fps = vidcap.get(cv2.CAP_PROP_FPS),
total_frames = vidcap.get(cv2.CAP_PROP_FRAME_COUNT)
height = int(vidcap.get(cv2.CAP_PROP_FRAME_HEIGHT))
width = int(vidcap.get(cv2.CAP_PROP_FRAME_WIDTH))

writer = cv2.VideoWriter("output2.mp4", cv2.VideoWriter_fourcc(*'mp4v'), video_fps[0], (int(width), int(height)))

count = 0
time = 0
window_size = round(window * video_fps[0]) # window size in frames
frame_time = (1 / video_fps[0]) * 1000 # milliseconden
window *= 1000 # window in milliseconden

def get_heatmap(df, bins, filter):

    heatmap, xedges, yedges = np.histogram2d(df['FixationPointX'] * 1280, df['FixationPointY'] * 720, bins=bins)
    #heatmap *= 255
    heatmap = heatmap.astype(np.uint8).T
    #heatmap = 255 - heatmap
    heatmap = gaussian_filter(heatmap, sigma=filter)
    heatmap = cv2.applyColorMap(heatmap, cv2.COLORMAP_JET)
    heatmap[np.where((heatmap==[0, 0, 128]).all(axis=2))] = [0, 0, 0]

    return heatmap

def process_image(frame, frameCount):
    window_start = frameCount * frame_time
    window_end = frameCount * frame_time + window
    
    if df.iloc[-1, df.columns.get_loc('Start')] < (window_start - window):
        return None

    data = df.loc[(df['Start'] > window_start) & (df['Start'] < window_end)]
    heatmap = get_heatmap(data, (width, height), 7)
    
    return cv2.addWeighted(frame, 1, heatmap, 1, 0)

while success:   

    result = process_image(frame, count) # process current frame

    if result is None:
        break

    writer.write(result) # write frame to output
    success, frame = vidcap.read()

    print(f"Processing video {round((count / total_frames) * 100)}% done    ", end='\r')
    count += 1

print("\n Done!")
vidcap.release()
writer.release()