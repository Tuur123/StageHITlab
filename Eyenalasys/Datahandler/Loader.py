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

            export = pd.read_csv(self.data_file)
            export['X'] = export['norm_pos_x'] * self.world_width
            export['Y'] = self.world_height - export['norm_pos_y'] * self.world_height

            final_dataset = data_to_convert = export.astype({'world_index': int, 'X': int, 'Y': int})

        if self.tracker == 'tobii':

            export = pd.read_csv(self.data_file, sep='\t')
            final_dataset = export

            # timestamp in microseconds: / 1000
            export['Recording timestamp'] = export['Recording timestamp']
            export['world_index'] = None

            # convert timestamps into frame indeces
            window_start = 0
            for frame_idx in range(self.total_frames):
                                
                window_end = self.frame_time * frame_idx + self.frame_time

                indeces = export.index[(export['Recording timestamp'] >= window_start) & (export['Recording timestamp'] < window_end)]
                export.iloc[indeces, export.columns.get_loc('world_index')] = frame_idx

                window_start = window_end


            export.dropna(inplace=True, subset=['Gaze point X', 'Gaze point Y']) # drop NA from original dataset

            export['X'] = np.array(export['Gaze point X'].values).astype(np.uint16)
            export['Y'] = np.array(export['Gaze point Y'].values).astype(np.uint16)

            data_to_convert = export[['world_index', 'X', 'Y']]


        self.converter = Convert2DGPU(data_to_convert, self.world_panorama, self.vidcap, self.message_q)
        converted_data = self.converter.Get2D()

        final_dataset['world_index'] = converted_data['world_index']
        final_dataset['X'] = converted_data['X']
        final_dataset['Y'] = converted_data['Y']
        final_dataset.dropna(inplace=True, subset=['X', 'Y']) # drop NA from original dataset


        if self.export: # create converted_data export

            final_dataset.to_csv(self.export, index=False)

            print(f"mean: {final_dataset['X'].mean()} {final_dataset['Y'].mean()}, std: {final_dataset['X'].std()} {final_dataset['Y'].std()}")


        self.running = False

        self.message_q.put('Done')
        self.message_q.put(final_dataset)