import os
import threading
import time
import tkinter as tk
from tkinter import EW, NW, Canvas, E, StringVar, filedialog
from tkinter.messagebox import showinfo

import cv2
import numpy as np
import pandas as pd
from tkinter.ttk import Combobox
from PIL import Image, ImageTk

from HeatmapMaker import HeatmapMaker


class GUI(tk.Tk):

    def __init__(self):
        super().__init__()

        self.img = ImageTk.PhotoImage(file='./assets/placeholder.png')
        self.canvas = Canvas(self, width = 520, height = 360)
        self.canvas.grid(rowspan=5, column=0)    
        self.container = self.canvas.create_image(20, 20, anchor=NW, image=self.img)
        
        self.tsv_btn = tk.Button(self, text='Select your data file')
        self.tsv_btn.grid(row=0, column=2, padx=5, sticky=EW)  
        self.tsv_btn['command'] = self.get_data
        
        self.vid_btn = tk.Button(self, text='Select your mp4 file')
        self.vid_btn.grid(row=1, column=2, padx=5, sticky=EW)  
        self.vid_btn['command'] = self.get_vid

        self.filter_label = tk.Label(text="Filter value:", anchor=E)
        self.filter_label.grid(row=2, column=1, sticky=E)
        self.filter_value = tk.IntVar()
        self.filter_value.set(7)
        self.filter_entry = tk.Spinbox(self, from_=0, to=50, increment=1, textvariable=self.filter_value)
        self.filter_entry.grid(row=2, column=2, sticky=EW, padx=5)
        
        self.tracker_label = tk.Label(text="Tracker type:", anchor=E)
        self.tracker_label.grid(row=3, column=1, sticky=E)
        self.tracker_combo = Combobox(self, values=['pupillabs', 'tobii'])
        self.tracker_combo.set('tobii')
        self.tracker_combo.grid(row=3, column=2, sticky=EW, padx=5)

        self.pan_btn = tk.Button(self, text='Select panorama file')
        self.pan_btn.grid(row=4, column=2, padx=5, sticky=EW)  
        self.pan_btn['command'] = self.get_panorama

        self.export_btn = tk.Button(self, text='Export')
        self.export_btn.grid(row=6, columnspan=5, pady=10, padx=10, sticky=EW)  
        self.export_btn['command'] = self.start

        self.data_file = None
        self.video_file = None
        self.panorama_file = None

    def start(self):
        
        if self.data_file is None or self.video_file is None or self.panorama_file is None:
            showinfo("Error", "Select data and video file please.")
            return

        self.hm = HeatmapMaker(self.data_file, self.video_file, self.tracker_combo.get(), panorama=self.panorama_file)
        self.hm.make_heatmap()

    def get_data(self):
        self.data_file = filedialog.askopenfilename()
        print(self.data_file)
        self.tsv_btn['text'] = os.path.basename(self.data_file)

    def get_vid(self):
        self.video_file = filedialog.askopenfilename()
        print(self.video_file)
        self.vid_btn['text'] = os.path.basename(self.video_file)

    def get_panorama(self):
        self.panorama_file = filedialog.askopenfilename()
        print(self.panorama_file)
        self.pan_btn['text'] = os.path.basename(self.panorama_file)

    def updateUI(self):
        
        while True:
            time.sleep(0.2)
            try:
                img = self.hm.result

                if len(img) != 0 or img != None:
                
                    img = cv2.resize(self.hm.result, (280, 200))
                    img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
                    img = Image.fromarray(img)

                    self.img = ImageTk.PhotoImage(image=img)
                    self.canvas.itemconfig(self.container, image=self.img)

                if self.progress(self.hm.percent_done) or not self.updating:
                    break

            except Exception as e:
                print(e)

if __name__ == "__main__":
    app = GUI()
    app.mainloop()