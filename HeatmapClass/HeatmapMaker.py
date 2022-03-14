import cv2
import numpy as np
from Converter import Convert2D
from imutils.Panorama import Panorama
from scipy.ndimage import gaussian_filter

import matplotlib.pyplot as plt

class HeatmapMaker:

    def __init__(self, data, video, panorama, tracker, threads=5, scaling=1, panorama_name=None, filter=7) -> None:


        if panorama: # panorama not None -> expect data from mobile eyetracker

            if panorama == 'create':
                print("Creating panorama. This can take a while...\n")
                panorama_maker = Panorama(video, panorama_name, (self.world_width // scaling, self.world_height // scaling))
                self.world_panorama = panorama_maker.Create_Panorama()
            else:
                self.world_panorama = cv2.imread(panorama)

            self.pan_height, self.pan_width, _ = self.world_panorama.shape
            self.filter = filter
            self.converter = Convert2D(data, video, self.world_panorama, tracker, threads)
            self.data = self.converter.Get2D()

    def make_heatmap(self):

        heatmap, xedges, yedges = np.histogram2d(self.data['X'], self.data['Y'], bins=(self.pan_width, self.pan_height), range=[[0, self.pan_width], [0, self.pan_height]])
        heatmap *= 255
        heatmap = heatmap.astype(np.uint8).T
        heatmap = gaussian_filter(heatmap, self.filter)
        heatmap = heatmap.astype(np.uint8)

        heatmap = cv2.applyColorMap(heatmap, cv2.COLORMAP_HSV)
        heatmap[np.where((heatmap==heatmap[heatmap.shape[0]-1]).all(axis=2))] = [0, 0, 0]

        return heatmap, cv2.resize(self.world_panorama, (heatmap.shape[1], heatmap.shape[0]))



if __name__ == "__main__":
    map = HeatmapMaker('./waak/data.tsv', './waak/waak.mp4', './waak/waak_panorama.png', 'tobii', filter=3)
    heatmap, pan = map.make_heatmap()



    heatmap = cv2.addWeighted(pan, 1, heatmap, 1, 0.5)
    
    plt.imshow(heatmap)
    plt.show()