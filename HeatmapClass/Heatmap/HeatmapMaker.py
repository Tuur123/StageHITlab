import cv2
import numpy as np
import pandas as pd
from Converter import Convert2D
from ConverterGPU import Convert2DGPU
from Panorama import Panorama
from scipy.ndimage import gaussian_filter

import time
import matplotlib.pyplot as plt

class HeatmapMaker:

    def __init__(self, data=None, video=None, tracker='tobii', export=None, threads=4, scaling=1, panorama_name=None, filter=7, panorama='create', gpu=True) -> None:

        if panorama: # panorama not None -> expect data from mobile eyetracker

            if panorama == 'create':
                print("Creating panorama. This can take a while...\n")
                panorama_maker = Panorama(video, panorama_name, scaling)
                self.world_panorama = panorama_maker.Create_Panorama()
            else:
                self.world_panorama = cv2.imread(panorama)

            self.pan_height, self.pan_width, _ = self.world_panorama.shape
            self.filter = filter
            
            if export is None: # create data export

                if gpu:
                    self.converter = Convert2DGPU(data, video, self.world_panorama, tracker)
                else:
                    self.converter = Convert2D(data, video, self.world_panorama, tracker, threads)

                self.data = self.converter.Get2D()

                print(f"mean: {self.data['X'].mean()} {self.data['Y'].mean()}, std: {self.data['X'].std()} {self.data['Y'].std()}")

            else:
                self.data = pd.read_csv(export)

            self.x_min = self.data['X'].min()
            self.x_max = self.data['X'].max()

            self.y_min = self.data['Y'].min()
            self.y_max = self.data['Y'].max()

    def make_heatmap(self):

        heatmap, xedges, yedges = np.histogram2d(self.data['X'], self.data['Y'], bins=(self.pan_width, self.pan_height), range=[[0, self.pan_width], [0, self.pan_height]])
        heatmap *= 255
        heatmap = heatmap.astype(np.uint8).T
        heatmap = gaussian_filter(heatmap, self.filter)
        heatmap = heatmap.astype(np.uint8)
 
        heatmap = cv2.applyColorMap(heatmap, cv2.COLORMAP_HSV)
        heatmap[np.where((heatmap==heatmap[heatmap.shape[0]-1]).all(axis=2))] = [0, 0, 0]
        heatmap[np.where((heatmap==[0, 0, 255]).all(axis=2))] = [0, 0, 0]

        return heatmap, cv2.resize(self.world_panorama, (heatmap.shape[1], heatmap.shape[0]))



def timeit():

    start = time.time()
    map = HeatmapMaker('./waak/data.tsv', './waak/waak.mp4', 'tobii', panorama='./waak/waak_panorama.png', filter=7, gpu=False)
    heatmap, pan = map.make_heatmap()

    cpu_time = time.time() - start

    print(f"CPU Time: {cpu_time}")

    start = time.time()
    map = HeatmapMaker('./waak/data.tsv', './waak/waak.mp4', 'tobii', panorama='./waak/waak_panorama.png', filter=7, gpu=True)
    heatmap, pan = map.make_heatmap()

    gpu_time = time.time() - start

    print(f"GPU Time: {gpu_time}")


if __name__ == "__main__":


    # map = HeatmapMaker(export='./waak/gpuwaak.csv', panorama='./waak/waak_panorama.png')
    # map = HeatmapMaker('./pupillabs/gaze_positions.csv', './pupillabs/world.mp4', 'pupillabs', panorama='./pupillabs/panorama.png', filter=7, gpu=True)     

    # heatmap, pan = map.make_heatmap()
    # heat = cv2.addWeighted(pan, 1, heatmap, 1, 0)
    # plt.imshow(heat)
    # plt.show()

    # cv2.imwrite(f"test.png", heat)


    map = HeatmapMaker('./waak/data.tsv', './waak/video.mp4', 'tobii', panorama='./waak/waak_panorama.png', filter=7, gpu=True)     
    heatmap, pan = map.make_heatmap()
    heat = cv2.addWeighted(pan, 1, heatmap, 1, 0)
    cv2.imwrite(f"test.png", heat)

    # for i in range(10):

    #     map = HeatmapMaker('./waak/data.tsv', './waak/world.mp4', 'tobii', panorama='./waak/waak_panorama.png', filter=7, gpu=True)     

    #     heatmap, pan = map.make_heatmap()
    #     heat = cv2.addWeighted(pan, 1, heatmap, 1, 0)
    #     cv2.imwrite(f"{i}.png", heat)


    # timeit()