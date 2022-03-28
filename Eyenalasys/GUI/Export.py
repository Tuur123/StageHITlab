import sys

sys.path.insert(1, r'C:\Users\Arthur\Desktop\school\StageHITlab\Eyenalasys\Datahandler')

import threading
import tkinter as tk

from tkinter import messagebox
from tkinter.ttk import Progressbar

from Loader import Loader

class Export(tk.Tk):

    def __init__(self, data_file, video, tracker, panorama=None, export='export.csv', scaling=1):
        super().__init__()
        
        # window always on top
        self.attributes('-topmost', True)

        # global vars
        self.exported = None
        self.loader = Loader(data_file, video, tracker, panorama, export)

        # progressbar
        self.progress_bar = Progressbar(self, orient='horizontal', mode='determinate')
        self.progress_bar.pack()
        
        # update thread
        self.update_thread = threading.Thread(target=self.updateUI)
        self.update_thread.start()

    def progress(self, value):
        if self.progress_bar['value'] < 100:
            self.progress_bar['value'] = value
            return False
        else:
            messagebox.showinfo(message='Done!')
            return True
 
    def updateUI(self):
        
        while True:
            try:
                percent_done = (self.loader.converter.frame_idx // self.loader.total_frames) * 100

                if self.progress(percent_done):
                    self.exported = self.loader.data

            except Exception as e:
                print(e)

    def show(self):
        self.wait_window()
        return self.exported




if __name__ == "__main__":
    app = Export()
    app.mainloop()