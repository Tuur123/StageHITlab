import cv2
from matplotlib.pyplot import sca
import pandas as pd
import numpy as np

from Datahandler.Panorama import Panorama
from Datahandler.ConverterGPU import Convert2DGPU

class Loader:
    
    def __init__(self, data_file, video, tracker, panorama='create', export=None, scaling=1) -> None:

        self.vidcap = cv2.VideoCapture(video)
        self.video_fps = self.vidcap.get(cv2.CAP_PROP_FPS)
        self.total_frames = int(self.vidcap.get(cv2.CAP_PROP_FRAME_COUNT))
        self.world_height = int(self.vidcap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        self.world_width = int(self.vidcap.get(cv2.CAP_PROP_FRAME_WIDTH))
        self.frame_time = (1 / self.video_fps) * 1000 # milliseconden

        self.data_file = data_file
        self.tracker = tracker
        self.panorama = panorama
        self.export = export
        self.scaling = scaling


    def load(self):

        if self.tracker == 'pupillabs':

            df = pd.read_csv(self.data_file)
            df['X'] = df['norm_pos_x'] * self.world_width
            df['Y'] = self.world_height - df['norm_pos_y'] * self.world_height
            df = df[['world_index', 'X', 'Y']]

            self.data= df.astype({'world_index': int, 'X': int, 'Y': int})

        if self.tracker == 'tobii':

            df = pd.read_csv(self.data_file, sep='\t')

            df = df[['Recording timestamp', 'Gaze point X', 'Gaze point Y']]

            if df['Recording timestamp'][0] != 0: # we need to make sure timestamps start at 0
                df['Recording timestamp'] = (df['Recording timestamp'] - df['Recording timestamp'][0])

            # timestamp in microseconds: / 1000
            df['Recording timestamp'] = df['Recording timestamp'] / 1000


            df['world_index'] = None

            # convert timestamps into frame indeces
            window_start = 0
            for frame_idx in range(self.total_frames):
                                
                window_end = self.frame_time * frame_idx + self.frame_time

                indeces = df.index[(df['Recording timestamp'] >= window_start) & (df['Recording timestamp'] < window_end)]
                df.iloc[indeces, [3]] = frame_idx

                window_start = window_end

            df['X'] = np.array(df['Gaze point X'].values).astype(np.uint16)
            df['Y'] = np.array(df['Gaze point Y'].values).astype(np.uint16)

            # df['world_index'] = np.array(df['world_index'].values).astype(np.uint16)
            self.data = df[['world_index', 'X', 'Y']]
            self.data = self.data.loc[~(self.data[['X', 'Y']]==0).all(axis=1)]

        if self.panorama: # panorama not None -> expect data from mobile eyetracker


            self.world_panorama = cv2.imread(self.panorama)

            self.pan_height, self.pan_width, _ = self.world_panorama.shape
            
            if self.export is None: # create data export

                self.converter = Convert2DGPU(self.data, self.world_panorama, self.vidcap)
                self.data = self.converter.Get2D()

            else:
                self.data = pd.read_csv(self.export)

            print(f"mean: {self.data['X'].mean()} {self.data['Y'].mean()}, std: {self.data['X'].std()} {self.data['Y'].std()}")

            return self.data, True