import os
import threading
import time
import tkinter as tk
from tkinter import EW, NW, Canvas, E, StringVar, filedialog
from tkinter.messagebox import showinfo
from tkinter.ttk import Progressbar

import cv2
import numpy as np
import pandas as pd
from PIL import Image, ImageTk

from heatmapMaker import HeatmapMaker


class HeatmapGUI(tk.Tk):

    def __init__(self):
        super().__init__()

        self.updating = False
        self.update_thread = threading.Thread(target=self.updateUI)
        self.valid_columns = ['Recording timestamp', 'Recording resolution width', 'Recording resolution height', 'Participant name', 'Gaze point X', 'Gaze point Y']

        self.img = ImageTk.PhotoImage(file='placeholder.png')
        self.canvas = Canvas(self, width = 280, height = 200)
        self.canvas.grid(rowspan=5, column=0)    
        self.container = self.canvas.create_image(20, 20, anchor=NW, image=self.img)
        
        self.filter_label = tk.Label(text="Filter value:", anchor=E)
        self.filter_label.grid(row=2, column=1, sticky=E)
        self.filter_entry = tk.Entry()
        self.filter_entry.grid(row=2, column=2, sticky=EW, padx=5)  
        
        self.window_label = tk.Label(text="Window value:")
        self.window_label.grid(row=3, column=1)  
        self.window_entry = tk.Entry()
        self.window_entry.grid(row=3, column=2, padx=5, sticky=EW)  
                
        self.tsv_btn = tk.Button(self, text='Select your tsv file')
        self.tsv_btn.grid(row=0, column=2, padx=5, sticky=EW)  
        self.tsv_btn['command'] = self.get_tsv
        
        self.vid_btn = tk.Button(self, text='Select your mp4 file')
        self.vid_btn.grid(row=1, column=2, padx=5, sticky=EW)  
        self.vid_btn['command'] = self.get_vid
        
        self.export_btn = tk.Button(self, text='Export')
        self.export_btn.grid(row=6, columnspan=5, pady=10, padx=10, sticky=EW)  
        self.export_btn['command'] = self.start

        self.stop_btn = tk.Button(self, text='Stop')
        self.stop_btn.grid(row=7, columnspan=5, pady=10, padx=10, sticky=EW)  
        self.stop_btn['command'] = self.stop
        self.stop_btn['state'] ='disabled'

        self.progress_bar = Progressbar(self, orient='horizontal', mode='determinate')
        self.progress_bar.grid(row=8, column = 0, columnspan=5, padx=5, pady=5, sticky=EW)

    def get_tsv(self):

        self.tsv = filedialog.askopenfilename()

        # check if file is correct
        try:
            df = pd.read_csv(self.tsv, sep='\t')
            if not all(col in df.columns for col in self.valid_columns):
                raise Exception
        except:
            print("Not a valid tsv file")
            return

        self.tsv_btn['text'] = os.path.basename(self.tsv)
        self.participants = np.append(df['Participant name'].unique(), 'all')

        self.participants_stringvar = StringVar(self)
        self.participants_stringvar.set(self.participants[0]) # default value

        self.participant_label = tk.Label(text="name or 'all':")
        self.participant_label.grid(row=4, column=1)  
        self.participant_menu = tk.OptionMenu(self, self.participants_stringvar, *self.participants)
        self.participant_menu.grid(row=4, column=2, padx=5, sticky=EW)  

    def get_vid(self):
        self.vid = filedialog.askopenfilename()
        self.vid_btn['text'] = os.path.basename(self.vid)

    def start(self):
        
        try:

            window = int(self.window_entry.get())
            filter = int(self.filter_entry.get())

            if window < 0:
                window = False

        except ValueError:
            print("Filter en window moeten integers zijn")
            return


        self.hm = HeatmapMaker(filter, window, self.participants_stringvar.get(), self.tsv, self.vid)
        self.hm.start()
        self.stop_btn['state'] ='normal'
        self.export_btn['state'] = 'disabled'

        self.updating = True
        self.update_thread.start()

    def stop(self):
        self.hm.stop()
        self.stop_btn['state'] ='disabled'
        self.export_btn['state'] = 'normal'
        self.updating = False

    def progress(self, value):
        if self.progress_bar['value'] < 100:
            self.progress_bar['value'] = value
        else:
            self.stop()
            showinfo(message='Done!')

    def updateUI(self):

        
        while self.updating:

            time.sleep(0.2)
            try:
                img = self.hm.result

                if len(img) != 0 or img != None:
                
                    img = cv2.resize(self.hm.result, (280, 200))
                    img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
                    img = Image.fromarray(img)

                    self.img = ImageTk.PhotoImage(image=img)
                    self.canvas.itemconfig(self.container, image=self.img)

                self.progress(self.hm.percent_done)

            except Exception as e:
                print(e)

if __name__ == "__main__":
    app = HeatmapGUI()
    app.mainloop()