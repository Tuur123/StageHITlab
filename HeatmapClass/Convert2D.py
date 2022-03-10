import threading
import cv2
import numpy as np
import pandas as pd
from queue import Queue
from multiprocessing.pool import ThreadPool
from imutils.Panorama import Panorama

class Convert2D:

    def __init__(self, data, video, panorama, tracker, threads):

        if panorama == None:
            print("Creating panorama. This can take a while...")
            panorama_maker = Panorama(video, None)
            self.world_panorama = panorama_maker.Create_Panorama()
        else:
            self.world_panorama = cv2.imread(panorama)

        self.vidcap = cv2.VideoCapture(video)
        self.video_fps = self.vidcap.get(cv2.CAP_PROP_FPS)
        self.total_frames = int(self.vidcap.get(cv2.CAP_PROP_FRAME_COUNT))
        self.world_height = int(self.vidcap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        self.world_width = int(self.vidcap.get(cv2.CAP_PROP_FRAME_WIDTH))

        if tracker == 'pupillabs':

            df = pd.read_csv(data)
            df['X'] = df['norm_pos_x'] * self.world_width
            df['Y'] = self.world_height - df['norm_pos_y'] * self.world_height
            df = df[['world_index', 'X', 'Y']]

            self.data= df.astype({'world_index': int, 'X': int, 'Y': int})

        # Initiate SIFT detector
        self.sift = cv2.SIFT_create()

        FLANN_INDEX_KDTREE = 1
        self.MIN_MATCH_COUNT = 10
        index_params = dict(algorithm = FLANN_INDEX_KDTREE, trees = 5)
        search_params = dict(checks = 50)
        self.flann = cv2.FlannBasedMatcher(index_params, search_params)

        self.world_panorama = cv2.resize(self.world_panorama, (1400, self.world_height))

        self.thread_count = threads
        self.queue = Queue(maxsize=100)

    def Get2D(self):

        pool = ThreadPool(self.thread_count)
        fill_thread = threading.Thread(target=self.QueueFiller)
        fill_thread.start()

        results = []
        for i in range(0, self.thread_count):
            results.append(pool.apply_async(self.Convert))

        pool.close()
        pool.join()

        results = [r.get() for r in results]

        tmp = []
        for r in results:
            tmp.extend(r)

        df = pd.DataFrame(tmp, columns=['world_index', 'X', 'Y'])
        df = df.set_index('world_index')
        df = df.astype({'X': int, 'Y': int})
        
        return df.sort_index()

    def QueueFiller(self):

        success, frame = self.vidcap.read()
        frame_idx = 0
        while success:
            self.queue.put([frame_idx, frame])
            success, frame = self.vidcap.read()
            frame_idx += 1

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
    convert = Convert2D('./pupillabs/gaze_positions.csv', './pupillabs/world.mp4', './pupillabs/panorama.png', 'pupillabs', 5)

    results = convert.Get2D()

    print(results.head())