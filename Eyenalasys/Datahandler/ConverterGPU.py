import threading
import cv2
import numpy as np
import pandas as pd
from queue import Queue


class Convert2DGPU:

    def __init__(self, data, panorama, vidcap):

        self.data = data
        self.vidcap = vidcap
        self.world_panorama = panorama

        # Initiate matcher
        self.matcher = cv2.cuda.DescriptorMatcher_createBFMatcher(cv2.NORM_L2)
        self.MIN_MATCH_COUNT = 10

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

        while self.queue.qsize() < (self.queue.maxsize // 4): # wait for queue to fill up
            pass

        results = self.Convert()
        self.updating = False

        data = pd.DataFrame(results, columns=['world_index', 'X', 'Y'])
        data = data.dropna()

        return data

    def QueueFiller(self):

        success, frame = self.vidcap.read()
        frame_idx = 0

        while success:

            data = self.data.loc[(self.data['world_index'] == frame_idx)].to_numpy()
            self.queue.put([frame_idx, frame, data])

            success, frame = self.vidcap.read()
            frame_idx += 1

        self.vidcap.release()
            
    def Convert(self):

        frame_stream = cv2.cuda_Stream()
        results = []

        while not self.queue.qsize() == 0:

            self.frame_idx, frame, data = self.queue.get()

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

                    for points in data:
                        pan_x, pan_y = cv2.perspectiveTransform(np.float32([[points[1], points[2]]]).reshape(-1,1,2), M)[0][0]
                        results.append([self.frame_idx, int(pan_x), int(pan_y)])

                    # pan_x, pan_y = cv2.perspectiveTransform(np.float32([[data[0][1], data[0][2]]]).reshape(-1,1,2), M)[0][0]
                    # results.append([frame_idx, int(pan_x), int(pan_y)])
        
                else:
                    results.append([self.frame_idx, None, None])
            else:
                results.append([self.frame_idx, None, None])

        return results


if __name__ == "__main__":

    # convert = Convert2DGPU('./pupillabs/gaze_positions.csv', './pupillabs/world.mp4', './pupillabs/panorama.png', 'pupillabs')
    convert = Convert2DGPU('./waak/data.tsv', './waak/waak.mp4', './waak/waak_panorama.png', 'tobii')

    results = convert.Get2D()
    print("\nProcessing done...")


    print(results.head())

    results.to_csv('gpuwaak.csv')