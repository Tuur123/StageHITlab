import cv2
import numpy as np
from scipy.ndimage import gaussian_filter

class HeatmapMaker:

    def __init__(self, panorama, data=None, filter=7) -> None:

        self.data = data
        self.filter = filter
        self.world_panorama = cv2.imread(panorama)
        self.pan_width, self.pan_height, _ = self.world_panorama.shape
        
        self.x_min = self.data['X'].min()
        self.x_max = self.data['X'].max()

        self.y_min = self.data['Y'].min()
        self.y_max = self.data['Y'].max()

    def make_heatmap(self):

        heatmap, xedges, yedges = np.histogram2d(self.data['X'], self.data['Y'], bins=(self.pan_width, self.pan_height), range=[[0, self.pan_width], [0, self.pan_height / 2]])
        heatmap *= 255
        heatmap = heatmap.astype(np.uint8).T
        heatmap = gaussian_filter(heatmap, self.filter)
        heatmap = heatmap.astype(np.uint8)
 
        heatmap = cv2.applyColorMap(heatmap, cv2.COLORMAP_HSV)
        heatmap[np.where((heatmap==heatmap[heatmap.shape[0]-1]).all(axis=2))] = [0, 0, 0]
        heatmap[np.where((heatmap==[0, 0, 255]).all(axis=2))] = [0, 0, 0]

        final = cv2.addWeighted(cv2.resize(self.world_panorama, (heatmap.shape[1], heatmap.shape[0])), 1, heatmap, 1, 0)
        return final