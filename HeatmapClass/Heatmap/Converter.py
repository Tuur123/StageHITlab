import threading
import cv2
import numpy as np
import pandas as pd
from queue import Queue
from multiprocessing.pool import ThreadPool

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

class Convert2D(DataHandler):

    def __init__(self, data, video, panorama, tracker, threads):

        super().__init__(data, video, tracker)

        self.world_panorama = panorama

        # Initiate SIFT detector
        self.sift = cv2.SIFT_create()

        FLANN_INDEX_KDTREE = 1
        self.MIN_MATCH_COUNT = 10
        index_params = dict(algorithm = FLANN_INDEX_KDTREE, trees = 5)
        search_params = dict(checks = 50)
        self.flann = cv2.FlannBasedMatcher(index_params, search_params)
        
        self.frame_idx = 0
        self.thread_count = threads
        self.queue = Queue(maxsize=200)
        
    def Get2D(self):

        pool = ThreadPool(self.thread_count)

        fill_thread = threading.Thread(target=self.QueueFiller)
        fill_thread.start()

        update_thread = threading.Thread(target=self.UpdateUI)
        update_thread.setDaemon(True)
        update_thread.start()

        results = []
        for _ in range(0, self.thread_count):
            results.append(pool.apply_async(self.Convert))

        pool.close()
        pool.join()

        results = [r.get() for r in results]

        tmp = []
        for r in results:
            tmp.extend(r)

        data = pd.DataFrame(tmp, columns=['world_index', 'X', 'Y'])
        data = data.fillna(0)
        data = data.astype({'X': int, 'Y': int})
        
        return data.sort_values('world_index')

    def QueueFiller(self):

        success, frame = self.vidcap.read()
        self.frame_idx = 0
        while success:
            self.queue.put([self.frame_idx, frame])
            success, frame = self.vidcap.read()
            self.frame_idx += 1
            print(f"         ", end='\r')
        self.vidcap.release()
    
    def UpdateUI(self):
        
        while self.queue.empty():
            pass # wait for q to fill up

        while not self.queue.empty():
            print(f"\rQueue size: {self.queue.qsize()}     Read {round((self.frame_idx / self.total_frames) * 100)}% of frames ", end='', flush=True)
        print()
        
    def Convert(self):

        results = []
        kp2, des2 = self.sift.detectAndCompute(self.world_panorama, None)

        while not self.queue.empty():

            frame_idx, frame = self.queue.get()

            # find the keypoints and descriptors with SIFT
            kp1, des1 = self.sift.detectAndCompute(frame, None)
            matches = self.flann.knnMatch(des1,des2,k=2)

            # store all the good matches as per Lowe's ratio test.
            good = []
            for m,n in matches:
                if m.distance < 0.7 * n.distance:
                    good.append(m)

            if len(good) > self.MIN_MATCH_COUNT:

                src_pts = np.float32([ kp1[m.queryIdx].pt for m in good ]).reshape(-1,1,2)
                dst_pts = np.float32([ kp2[m.trainIdx].pt for m in good ]).reshape(-1,1,2)

                M, _ = cv2.findHomography(src_pts, dst_pts, cv2.RANSAC, 5.0)
                _, x, y = self.data.loc[(self.data['world_index'] == frame_idx)].mean()
                pan_x, pan_y = cv2.perspectiveTransform(np.float32([[x, y]]).reshape(-1,1,2), M)[0][0]

                results.append([frame_idx, pan_x, pan_y])

            else:
                results.append([frame_idx, None, None])

        return results



if __name__ == "__main__":
    convert = Convert2D('./waak/data.tsv', './waak/waak.mp4', './waak/waak_panorama.png', 'tobii', 5, 4)

    results = convert.Get2D()
    results[0].to_csv('waak.csv')
    print("saved csv file")