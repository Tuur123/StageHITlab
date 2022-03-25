import os
import json
import tkinter as tk
from tkinter import EW, E, filedialog
from tkinter.messagebox import showinfo

from tkinter.ttk import Combobox


class Inputs(tk.Tk):

    def __init__(self):
        super().__init__()
        
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

        self.export_btn = tk.Button(self, text='Create project')
        self.export_btn.grid(row=6, columnspan=5, pady=10, padx=10, sticky=EW)  
        self.export_btn['command'] = self.start

        self.data_file = None
        self.video_file = None
        self.panorama_file = None

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

    def start(self):
        if self.data_file is None or self.video_file is None or self.panorama_file is None:
            showinfo("Error", "Please select valid files.")
            return

        values = dict({

            'video': self.video_file,
            'data': self.data_file,
            'panorama': self.panorama_file,
            'filter': self.filter_value.get(),
            'tracker': self.tracker_combo.get()
        })

        valus = json.dumps(values)

        with open('project.json', 'a') as f:
            f.write(valus)
            f.close()


        

if __name__ == "__main__":
    app = Inputs()
    app.mainloop()