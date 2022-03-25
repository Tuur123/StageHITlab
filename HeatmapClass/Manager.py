import threading

from Datahandler.Load import Loader



class Manager:

    def __init__(self):

        self.data = None
        self.loaded = False
        

    def load_data(self, data=None, video=None, export=None, tracker='tobii', panorama='create'):
        self.data_file = data
        self.video_file = video
        self.export_file = export
        self.tracker=tracker
        self.panorama=panorama

        self.loader = Loader(self.data_file, self.video_file, self.tracker, self.panorama, self.export_file)

        self.__loader_thread = threading.Thread(target=self.__loader)
        self.__loader_thread.start()


    def __loader(self):
        
        self.data, self.loaded = self.loader.load()


if __name__ == "__main__":

    man = Manager()

    man.load_data('./data/pupillabs/gaze_positions.csv', './data/pupillabs/world.mp4', 'pupillabs', './data/pupillabs/panorama.png', None)