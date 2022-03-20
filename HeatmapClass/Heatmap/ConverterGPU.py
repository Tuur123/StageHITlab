import threading
import cv2
from cv2 import cuda
import numpy as np
import pandas as pd
from queue import Queue

from sklearn.preprocessing import MinMaxScaler


class DataHandler:
    
    def __init__(self, data_file, video, tracker) -> None:

        self.vidcap = cv2.VideoCapture(video)
        self.video_fps = self.vidcap.get(cv2.CAP_PROP_FPS)
        self.total_frames = int(self.vidcap.get(cv2.CAP_PROP_FRAME_COUNT))
        self.world_height = int(self.vidcap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        self.world_width = int(self.vidcap.get(cv2.CAP_PROP_FRAME_WIDTH))
        self.frame_time = (1 / self.video_fps) * 1000 # milliseconden

        if tracker == 'pupillabs':

            df = pd.read_csv(data_file)
            df['X'] = df['norm_pos_x'] * self.world_width
            df['Y'] = self.world_height - df['norm_pos_y'] * self.world_height
            df = df[['world_index', 'X', 'Y']]

            self.data= df.astype({'world_index': int, 'X': int, 'Y': int})

        if tracker == 'tobii':

            df = pd.read_csv(data_file, sep='\t')

            df = df[['Recording timestamp', 'Gaze point X', 'Gaze point Y']]

            if df['Recording timestamp'][0] != 0: # we need to make sure timestamps start at 0
                df['Recording timestamp'] = (df['Recording timestamp'] - df['Recording timestamp'][0]) / 1000

            df = df.loc[~(df[['Gaze point X', 'Gaze point Y']]==0).all(axis=1)]

            data = pd.DataFrame(columns=['world_index', 'Gaze point X', 'Gaze point Y'])

            # convert timestamps into frame indeces
            for frame_idx in range(self.total_frames):
                
                window_start = 0
                window_end = self.frame_time * frame_idx + self.frame_time

                tmp = df.loc[(df['Recording timestamp'] >= window_start) & (df['Recording timestamp'] < window_end)].mean()
                tmp['world_index'] = frame_idx

                data.loc[frame_idx] = tmp

                window_start = window_end

            data['X'] = np.array(data['Gaze point X'].values).astype(np.uint16)
            data['Y'] = np.array(data['Gaze point Y'].values).astype(np.uint16)
            data['world_index'] = np.array(data['world_index'].values).astype(np.uint16)
            self.data = data[['world_index', 'X', 'Y']]


class Convert2DGPU(DataHandler):

    def __init__(self, data, video, panorama, tracker):

        super().__init__(data, video, tracker)

        if type(panorama) == str:
            self.world_panorama = cv2.imread(panorama)
        else:
            self.world_panorama = panorama

        # Initiate matcher
        self.matcher = cv2.cuda.DescriptorMatcher_createBFMatcher(cv2.NORM_L2)
        self.MIN_MATCH_COUNT = 4

        # panorama stream
        pan_stream = cv2.cuda_Stream()

        # Initiate ORB detector
        self.surf = cv2.cuda.SURF_CUDA_create(300, _nOctaveLayers=2)

        # Load the image onto the GPU
        cuMat = cv2.cuda_GpuMat()
        cuMat.upload(self.world_panorama, pan_stream)

        # Convert the color on the GPU
        cuMat = cv2.cuda.cvtColor(cuMat, cv2.COLOR_BGR2GRAY, stream=pan_stream)

        # Create the CUDA ORB detector and detect keypoints/descriptors
        kp2, self.des2 = self.surf.detectWithDescriptors(cuMat, None)

        # Download the keypoints from the GPU memory
        self.kp2 = cv2.cuda_SURF_CUDA.downloadKeypoints(self.surf, kp2)
        pan_stream.waitForCompletion()

        self.frame_idx = 0
        self.queue = Queue(maxsize=200)
        self.updating = True
        self.results = []
    
    def Get2D(self):

        fill_thread = threading.Thread(target=self.QueueFiller)
        fill_thread.start()

        update_thread = threading.Thread(target=self.UpdateUI)
        update_thread.start()

        while self.queue.qsize() < (self.queue.maxsize // 4): # wait for queue to fill up
            pass

        results = self.Convert()
        self.updating = False

        data = pd.DataFrame(results, columns=['world_index', 'X', 'Y'])
        data = data.fillna(0)

        data = data.astype({'X': int, 'Y': int})
        
        df = data.loc[~(data[['X', 'Y']]==0).all(axis=1)]
        print(len(df) / len(data))

        return data

    def QueueFiller(self):

        success, frame = self.vidcap.read()
        self.frame_idx = 0

        while success:

            _, x, y = self.data.loc[(self.data['world_index'] == self.frame_idx)].mean()
            self.queue.put([self.frame_idx, frame, x, y])

            success, frame = self.vidcap.read()
            self.frame_idx += 1

        self.vidcap.release()
    
    def UpdateUI(self):
        
        while self.queue.empty():
            pass # wait for q to fill up

        while not self.queue.qsize() == 0 and self.updating:
            print(f"\rQueue size: {self.queue.qsize()}     Read {round((self.frame_idx / self.total_frames) * 100)}% of frames ", end='', flush=True)
        print(f"\rQueue size: {self.queue.qsize()}     Read {round((self.frame_idx / self.total_frames) * 100)}% of frames ", end='\n', flush=True)
        
    def Convert(self):

        frame_stream = cv2.cuda_Stream()
        results = []

        while not self.queue.qsize() == 0:

            frame_idx, frame, x, y = self.queue.get()

            # Load the image onto the GPU
            cuMatFrame = cv2.cuda_GpuMat()
            cuMatFrame.upload(frame, stream=frame_stream)

            # Convert the color on the GPU
            cuMatFrame = cv2.cuda.cvtColor(cuMatFrame, cv2.COLOR_BGR2GRAY, stream=frame_stream)

            # Detect keypoints/descriptors                
            kp1, des1 = self.surf.detectWithDescriptors(cuMatFrame, None)
            gpu_matches = self.matcher.knnMatchAsync(des1, self.des2, k=2, stream=frame_stream)

            # Download the keypoints and matches from GPU memory
            kp1 = cv2.cuda_SURF_CUDA.downloadKeypoints(self.surf, kp1)
            frame_stream.waitForCompletion()

            matches = self.matcher.knnMatchConvert(gpu_matches)

            # store all the good matches as per Lowe's ratio test.
            good = []
            for m, n in matches:
                if m.distance < 0.7 * n.distance:
                    good.append(m)

            if len(good) > self.MIN_MATCH_COUNT:

                src_pts = np.float32([ kp1[m.queryIdx].pt for m in good ]).reshape(-1,1,2)
                dst_pts = np.float32([ self.kp2[m.trainIdx].pt for m in good ]).reshape(-1,1,2)

                M, _ = cv2.findHomography(src_pts, dst_pts, cv2.RANSAC, 5.0)

                if M is not None:
                    pan_x, pan_y = cv2.perspectiveTransform(np.float32([[x, y]]).reshape(-1,1,2), M)[0][0]

                    results.append([frame_idx, pan_x, pan_y])

                else:
                    results.append([frame_idx, None, None])
            else:
                results.append([frame_idx, None, None])

        return results


if __name__ == "__main__":

    # convert = Convert2DGPU('./pupillabs/gaze_positions.csv', './pupillabs/world.mp4', './pupillabs/panorama.png', 'pupillabs')
    convert = Convert2DGPU('./waak/data.tsv', './waak/waak.mp4', './waak/waak_panorama.png', 'tobii')

    results = convert.Get2D()
    print("\nProcessing done...")


    print(results.head())

    df = results.loc[~(results[['X', 'Y']]==0).all(axis=1)]
    print(len(df) / len(results))

    results.to_csv('gpuwaak.csv')