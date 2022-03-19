import cv2
import numpy as np
from Converter import Convert2D
from ConverterGPU import Convert2DGPU
from Panorama import Panorama
from scipy.ndimage import gaussian_filter

import matplotlib.pyplot as plt

class HeatmapMaker:

    def __init__(self, data, video, tracker, threads=5, scaling=1, panorama_name=None, filter=7, panorama='create', gpu=False) -> None:

        if panorama: # panorama not None -> expect data from mobile eyetracker

            if panorama == 'create':
                print("Creating panorama. This can take a while...\n")
                panorama_maker = Panorama(video, panorama_name, scaling)
                self.world_panorama = panorama_maker.Create_Panorama()
            else:
                self.world_panorama = cv2.imread(panorama)

            self.pan_height, self.pan_width, _ = self.world_panorama.shape
            self.filter = filter

            if gpu:
                self.converter = Convert2DGPU(data, video, self.world_panorama, tracker)
            else:
                self.converter = Convert2D(data, video, self.world_panorama, tracker, threads)

            self.data = self.converter.Get2D()

            self.x_min = self.data['X'].min()
            self.x_max = self.data['X'].max()

            self.y_min = self.data['Y'].min()
            self.y_max = self.data['Y'].max()

    def make_heatmap(self):

        heatmap, xedges, yedges = np.histogram2d(self.data['X'], self.data['Y'], bins=(self.pan_width, self.pan_height), range=[[self.x_min, self.x_max], [self.y_min, self.y_max]])
        heatmap *= 255
        heatmap = heatmap.astype(np.uint8).T
        heatmap = gaussian_filter(heatmap, self.filter)
        heatmap = heatmap.astype(np.uint8)
 
        heatmap = cv2.applyColorMap(heatmap, cv2.COLORMAP_HSV)
        heatmap[np.where((heatmap==heatmap[heatmap.shape[0]-1]).all(axis=2))] = [0, 0, 0]

        return heatmap, cv2.resize(self.world_panorama, (heatmap.shape[1], heatmap.shape[0]))



if __name__ == "__main__":

    map = HeatmapMaker('./waak/data.tsv', './waak/waak.mp4', 'tobii', panorama='./waak/waak_panorama.png', filter=7, gpu=True)

    # map = HeatmapMaker('./pupillabs/gaze_positions.csv', './pupillabs/world.mp4', 'pupillabs', panorama='./pupillabs/panorama.png', filter=7, gpu=True)

    heatmap, pan = map.make_heatmap()
    heatmap = cv2.addWeighted(pan, 1, heatmap, 1, 0)
    
    plt.imshow(heatmap)
    plt.show()