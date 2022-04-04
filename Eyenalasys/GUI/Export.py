import threading
import gc

import tkinter as tk
from tkinter.ttk import Progressbar

from queue import Queue

from Datahandler.Loader import Loader


class ExportInfo(tk.Toplevel):

    def __init__(self, parameters):
        super().__init__()
        
        # window always on top
        self.attributes('-topmost', True)

        # progressbar
        self.progress_bar = Progressbar(self, orient='horizontal', mode='determinate')
        self.progress_bar.pack()

        # create message queue
        self.message_q = Queue()

        # vars
        self.running = True
        self.dataset = None
        self.loader = Loader(parameters, self.message_q)

        # message q thread
        self.message_handler_thread = threading.Thread(target=self.message_handler, name="ExportWindowMessageHandler")
        self.message_handler_thread.start()

    def message_handler(self):
        while self.running:

            try:
                message = self.message_q.get()
                
                if message == 'Done':
                    self.running = False
                    self.dataset = self.message_q.get()
                    self.destroy()
                    break    

                else:
                    self.progress_bar['value'] = message

            except Exception as e:
                print(e)
                break

    def get_data(self):
        self.wait_window()
        self.layout = None
        self.window = None
        self.tk = None
        gc.collect()
        return self.dataset

if __name__ == "__main__":
    app = ExportInfo()
    app.mainloop()