import os
import gc
import tkinter as tk
from tkinter import EW, E, filedialog
from tkinter.messagebox import showinfo

from tkinter.ttk import Combobox


class CreateProject(tk.Tk):

    def __init__(self):
        super().__init__()
        
        self.attributes('-topmost', True)

        self.values = None

        self.tsv_btn = tk.Button(self, text='Select your data file')
        self.tsv_btn['command'] = self.get_data
        self.tsv_btn.pack()

        self.vid_btn = tk.Button(self, text='Select your mp4 file') 
        self.vid_btn['command'] = self.get_vid
        self.vid_btn.pack()
        
        self.tracker_combo = Combobox(self, values=['pupillabs', 'tobii'])
        self.tracker_combo.set('tobii')
        self.tracker_combo.pack()

        self.pan_btn = tk.Button(self, text='Select panorama file') 
        self.pan_btn['command'] = self.get_panorama
        self.pan_btn.pack()

        self.project_fodler_btn = tk.Button(self, text='Select project folder') 
        self.project_fodler_btn['command'] = self.get_project_folder
        self.project_fodler_btn.pack()

        self.export_btn = tk.Button(self, text='Create project')  
        self.export_btn['command'] = self.create
        self.export_btn.pack()

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

    def get_project_folder(self):
        self.project_folder = filedialog.askdirectory()
        print(self.project_folder)
        self.project_fodler_btn['text'] = os.path.basename(self.project_folder)

    def create(self):
        if self.data_file is None or self.video_file is None or self.panorama_file is None:
            showinfo("Error", "Please select valid files.")
            return None

        self.values = dict({
            'files': dict({
                'video': self.video_file,
                'data': self.data_file,
                'panorama': self.panorama_file,
                'export': 'export.csv'}),
            'tracker': self.tracker_combo.get(),
            'project': self.project_folder})

        self.destroy()

    
    def show(self):
        self.wait_window()
        self.layout = None
        self.window = None
        self.tk = None
        gc.collect()
        return self.values

if __name__ == "__main__":
    app = CreateProject()
    app.mainloop()