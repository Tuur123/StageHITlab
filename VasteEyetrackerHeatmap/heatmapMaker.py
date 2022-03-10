import glob
import re
import threading

import time
import cv2
import numpy as np
import pandas as pd
from scipy.ndimage import gaussian_filter
from scipy.signal import convolve2d

class HeatmapMaker:

    def __init__(self, filter, window, participant, tsv, video):

        self.filter = filter
        self.window = window
        self.participant = participant
        self.result = None
        self.percent_done = None

        self.vidcap, self.df = self.__input(video, tsv)
        self.outputFile = self.__output()
        
        if self.window:
            self.window_size = round(self.window * self.video_fps[0]) # window size in frames

        self.frame_time = (1 / self.video_fps[0]) * 1000 # milliseconden
        self.frame_count = 0

        self.heatmap_thread = threading.Thread(target=self.__create_heatmap)

        self.running = False

    def start(self):

        if self.running:
            print("Thread alreasy running")
        else:
            self.running = True
            self.heatmap_thread.start()
            print("Started thread")

    def stop(self):
        if self.running:
            self.running = False
            print("Stopping thread")
        else:
            print("Thread already stopped")

    def __output(self):
        files = glob.glob('output*.mp4')
        if len(files) != 0:
            return int(re.findall(r'\d+', files[-1])[0].split('.')[0]) + 1
        else:
            return 0

    def __input(self, video, tsv):

        vidcap = cv2.VideoCapture(video)
        success, frame = vidcap.read()

        if not success:
            print("Video not found")
            exit(1)

        self.video_fps = vidcap.get(cv2.CAP_PROP_FPS),
        self.total_frames = vidcap.get(cv2.CAP_PROP_FRAME_COUNT)
        self.height = int(vidcap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        self.width = int(vidcap.get(cv2.CAP_PROP_FRAME_WIDTH))

        df = pd.read_csv(tsv, sep='\t')

        df['X'] = np.array(df['Gaze point X'].values).astype(np.uint16)
        df['Y'] = np.array(df['Gaze point Y'].values).astype(np.uint16)

        self.w = df['Recording resolution width'][0]
        self.h = df['Recording resolution height'][0]

        self.last_timestamp = df.iloc[-1, df.columns.get_loc('Recording timestamp')]

        return vidcap, df

    def __iter_convolve(self, img, iterations):
        gaussian = (1 / 16.0) * np.array([[1., 2., 1.], [2., 4., 2.], [1., 2., 1.]])
        
        for _ in range(iterations):
            img = convolve2d(img, gaussian, 'same', boundary = 'fill', fillvalue = 0)

        return img

    def __make_heatmap(self, x, y):

        heatmap, xedges, yedges = np.histogram2d(x, y, bins=(self.width, self.height), range=[[0, self.w], [0, self.h]])
        heatmap *= 255
        heatmap = heatmap.astype(np.uint8).T

        # heatmap = self.__iter_convolve(heatmap, 20)

        # gaussian = (1 / 16.0) * np.array([[1., 2., 1.], [2., 4., 2.], [1., 2., 1.]])
        # heatmap = np.apply_along_axis(lambda x: np.convolve(x, gaussian, mode='same'), 0, heatmap)
        # heatmap = np.apply_along_axis(lambda x: np.convolve(x, gaussian, mode='same'), 1, heatmap)

        heatmap = gaussian_filter(heatmap, self.filter)
        # heatmap = Gaussian2D(heatmap, self.filter)

        heatmap = heatmap.astype(np.uint8)

        heatmap = cv2.applyColorMap(heatmap, cv2.COLORMAP_HSV)
        heatmap[np.where((heatmap==heatmap[700][0]).all(axis=2))] = [0, 0, 0]

        return heatmap

    def __process_image(self, frame, count):

        window_start = 0

        if self.window:
            window_start = count * self.frame_time - (self.window // 2)

            if window_start < 0:
                window_start = 0

        window_end = count * self.frame_time + (self.window // 2)
            
        if self.last_timestamp < window_end:
            return None

        if self.participant == 'all':
            data = self.df.loc[(self.df['Recording timestamp'] > window_start) & (self.df['Recording timestamp'] < window_end) & ((self.df['Eye movement type'] == 'Fixation') | (self.df['Eye movement type'] == 'Saccade'))]
        else:
            data = self.df.loc[(self.df['Recording timestamp'] > window_start) & (self.df['Recording timestamp'] < window_end) & (self.df['Participant name'] == self.participant)]

        heatmap = self.__make_heatmap(data['X'], data['Y'])

        self.percent_done = round((window_end / self.last_timestamp) * 100)
        print(f"Processing video {self.percent_done}% done    ", end='\r')

        return cv2.addWeighted(frame, 1, heatmap, 1, 0)

    def __create_heatmap(self):
        self.writer = cv2.VideoWriter(f"output{self.outputFile}.mp4", cv2.VideoWriter_fourcc(*'mp4v'), self.video_fps[0], (self.width, self.height))
        success, frame = self.vidcap.read()
        count = 0

        while success:   

            self.result = self.__process_image(frame, count) # process current frame

            if self.result is None or not self.running:
                print("\n Done!")
                self.vidcap.release()
                self.writer.release()
                break

            self.writer.write(self.result) # write frame to output
            self.success, frame = self.vidcap.read()
            count += 1

    def __del__(self):
        if self.heatmap_thread.is_alive():
            self.running = False


if __name__ == "__main__":
    hm = HeatmapMaker(7, False, 'Jelle', 'video Data Export-ivt.tsv', 'vid.mp4')
    hm.start()
    time.sleep(10)
    hm.stop()