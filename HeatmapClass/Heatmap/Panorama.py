import cv2
import os
import shutil

class Panorama:

    def __init__(self, video, name, scaling):

        self.name = name
        self.folder = "frames/"
        if os.path.isdir(self.folder):
            shutil.rmtree(self.folder)
        os.mkdir(self.folder)

        # open vidcap
        self.cap = cv2.VideoCapture(video) # your video here
        self.scaling = scaling
        self.world_height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        self.world_width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    
    def Create_Panorama(self):
        self.Decimate()
        pan = self.Stitch()

        if pan is not None:
            return pan

    def Decimate(self):

        counter = 0

        length = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT))
        print(f"Total frames in file: {length}")

        # make an orb feature detector and a brute force matcher
        orb = cv2.ORB_create()
        bf = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=False)

        # store the first frame
        _, last = self.cap.read()
        last = self.__rescale(last)
        cv2.imwrite(self.folder + str(counter).zfill(5) + ".png", cv2.resize(last, (self.world_width // self.scaling, self.world_height // self.scaling)))

        # get the first frame's stuff
        kp1, des1 = orb.detectAndCompute(last, None)

        # cutoff, the minimum number of keypoints
        cutoff = 5
        # count number of frames
        prev = None
        while True:

            # get frame
            ret, frame = self.cap.read()
            if not ret:
                break

            # resize
            frame = self.__rescale(frame)

            # count keypoints
            kp2, des2 = orb.detectAndCompute(frame, None)

            try:
                # match
                matches = bf.knnMatch(des1, des2, k=2)
            except:
                continue
            
            # lowe's ratio
            good = []
            for m, n in matches:
                if m.distance < 0.5 * n.distance:
                    good.append(m)

            if len(good) < cutoff:
                # swap and save
                counter += 1
                last = frame
                kp1 = kp2
                des1 = des2
                cv2.imwrite(self.folder + str(counter).zfill(5) + ".png", cv2.resize(last, (self.world_width // self.scaling, self.world_height // self.scaling)))
                print("\rSaved " + str(counter) + " frames", end='', flush=True)

            prev = frame

        # also save last frame
        counter += 1
        cv2.imwrite(self.folder + str(counter).zfill(5) + ".png", cv2.resize(prev, (self.world_width // self.scaling, self.world_height // self.scaling)))
        
        self.cap.release()
    
    def __rescale(self, img):
        scale = 0.5
        h,w = img.shape[:2]
        h = int(h*scale)
        w = int(w*scale)
        return cv2.resize(img, (w,h))

    def Stitch(self):

        # use built in stitcher
        stitcher = cv2.Stitcher_create()

        # load images
        filenames = os.listdir(self.folder)
        images = []

        for file in filenames:
            # get image
            img = cv2.imread(self.folder + file)
            images.append(img)

        status, stitched = stitcher.stitch(images)

        if self.name == None:
            return stitched

        else:
            cv2.imwrite(self.name, stitched)
            return stitched


if __name__ == "__main__":
    pan = Panorama('waak/waak.mp4', 'waak/waak_panorama.png', 1)

    stiched = pan.Create_Panorama()