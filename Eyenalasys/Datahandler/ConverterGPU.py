import cv2
import threading
import numpy as np
import pandas as pd
from queue import Empty, Queue


class Convert2DGPU:

    def __init__(self, data, panorama, vidcap, message_q):

        self.data = data
        self.vidcap = vidcap
        self.world_panorama = panorama
        self.total_frames = int(self.vidcap.get(cv2.CAP_PROP_FRAME_COUNT))

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
        self.match_queue = Queue(maxsize=500)
        self.updating = True
        self.results = []
        self.done = False
        self.message_q = message_q
    
    def Get2D(self):

        fill_thread = threading.Thread(target=self.QueueFiller, name="Frame Queue filler")
        fill_thread.start()

        while self.queue.qsize() < (self.queue.maxsize // 4): # wait for queue to fill up
            pass

        convert_thread = threading.Thread(target=self.Convert, name="Convert Thread")
        convert_thread.start()

        results = self.Matcher()
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

            self.match_queue.put((matches, kp1, data))

        self.done = True

    def Matcher(self):

        results = []
        while not self.done or not self.match_queue.qsize() == 0:
 
            try:
                # print(f"Frame Q size: {self.queue.qsize()}. Convert Q size: {self.match_queue.qsize()}")
                matches, kp1, data = self.match_queue.get_nowait()
            except Empty:
                continue

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
            
            percent_done = round((self.frame_idx / self.total_frames) * 100)
            self.message_q.put(percent_done)

        return results