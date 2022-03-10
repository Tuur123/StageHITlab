from Converter import Convert2D




class HeatmapMaker:

    def __init__(self, data, video, panorama, tracker, threads) -> None:

        if panorama: # panorama not None -> expect data from mobile eyetracker

            converter = Convert2D(data, video, panorama, tracker, threads)
            self.data, self.panorama = converter.Get2D()
        
        







if __name__ == "__main__":
    map = HeatmapMaker('./pupillabs/gaze_positions.csv', './pupillabs/world.mp4', './pupillabs/panorama.png', 'pupillabs', 5)