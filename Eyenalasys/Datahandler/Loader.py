import cv2
import pandas as pd
import numpy as np
import threading

from Datahandler.ConverterGPU import Convert2DGPU

class Loader:
    
    def __init__(self, parameters, message_q) -> None:

        # read video file in
        self.vidcap = cv2.VideoCapture(parameters['files']['video'])
        self.video_fps = self.vidcap.get(cv2.CAP_PROP_FPS)
        self.total_frames = int(self.vidcap.get(cv2.CAP_PROP_FRAME_COUNT))
        self.world_height = int(self.vidcap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        self.world_width = int(self.vidcap.get(cv2.CAP_PROP_FRAME_WIDTH))
        self.frame_time = (1 / self.video_fps) * 1000 # milliseconden

        # vars
        self.data_file = parameters['files']['data']
        self.tracker = parameters['tracker']
        self.panorama = parameters['files']['panorama']
        self.export = parameters['files']['export']

        # messageq vars
        self.message_q = message_q
        self.running = True

        # read panorama in
        self.world_panorama = cv2.imread(self.panorama)
        self.pan_height, self.pan_width, _ = self.world_panorama.shape

        # start load thread
        self.load_thread = threading.Thread(target=self.__load, name="Loader Thread")
        self.load_thread.start()

    def __load(self):

        if self.tracker == 'pupillabs':

            df = pd.read_csv(self.data_file)
            df['X'] = df['norm_pos_x'] * self.world_width
            df['Y'] = self.world_height - df['norm_pos_y'] * self.world_height
            df = df[['world_index', 'X', 'Y']]

            data = df.astype({'world_index': int, 'X': int, 'Y': int})

        if self.tracker == 'tobii':

            df = pd.read_csv(self.data_file, sep='\t')

            df = df[['Recording timestamp', 'Gaze point X', 'Gaze point Y', 'Eye movement type']]

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
                df.iloc[indeces, [4]] = frame_idx

                window_start = window_end

            df['X'] = np.array(df['Gaze point X'].values).astype(np.uint16)
            df['Y'] = np.array(df['Gaze point Y'].values).astype(np.uint16)

            data = df[['world_index', 'X', 'Y']]
            data = data.loc[~(data[['X', 'Y']]==0).all(axis=1)]


        self.converter = Convert2DGPU(data, self.world_panorama, self.vidcap, self.message_q)
        converted_data = self.converter.Get2D()
        

        if self.export: # create converted_data export

            converted_data.to_csv(self.export, index=False)

            print(f"mean: {converted_data['X'].mean()} {converted_data['Y'].mean()}, std: {converted_data['X'].std()} {converted_data['Y'].std()}")

        self.running = False

        self.message_q.put('Done')
        self.message_q.put(converted_data)