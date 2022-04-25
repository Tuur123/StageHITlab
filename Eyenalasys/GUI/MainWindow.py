import json
import math
import time
import shutil
import pandas as pd
import threading

import tkinter as tk
from tkinter import *
from tkinter import ttk
from tkinter import messagebox, filedialog, simpledialog
from PIL import ImageTk, Image

from GUI.Export import ExportInfo
from GUI.CreateProject import CreateProject

from Heatmap.HeatmapMaker import HeatmapMaker


class MainWindow(tk.Tk):

    def __init__(self):
        super().__init__()

        # bind resize event
        self.attributes('-fullscreen', True)

        # set values 
        self.values = None
        self.dataset = None
        self.line_start_x = None
        self.line_start_y = None
        self.drawing = False
        self.aoi_list = []

        # create menu
        menubar = Menu(self)
        file_menu = Menu(menubar, tearoff=0)
        file_menu.add_command(label='New', command=self.new_project)       
        file_menu.add_command(label='Open', command=self.open_project)
        file_menu.add_command(label='Save', command=self.save)

        # add menu to menubar
        menubar.add_cascade(label='File', menu=file_menu)
        self.config(menu=menubar)

        # create tabs
        tab_control = ttk.Notebook(self)
        pan_tab = ttk.Frame(tab_control)
        data_tab = ttk.Frame(tab_control)
        heatmap_tab = ttk.Frame(tab_control)
        tab_control.add(pan_tab, text='Panorama')
        tab_control.add(heatmap_tab, text='Heatmap')
        tab_control.add(data_tab, text='Data')
        tab_control.pack(fill='both', expand=True)

        # create img container
        self.img = ImageTk.PhotoImage(file='./assets/placeholder.png')
        self.canvas = Canvas(pan_tab)
        self.canvas.bind('<Button-1>', self.canvas_click_handler)
        self.canvas.bind('<B1-Motion>', self.draw_motion)
        self.canvas.bind('<ButtonRelease-1>', self.canvas_click_release_handler)
        self.canvas.pack(fill='both', expand=True)
        self.container = self.canvas.create_image(0, 0, anchor=NW, image=self.img)

        # create heatmap container
        self.heatmap_canvas = Canvas(heatmap_tab)
        self.heatmap_canvas.pack(fill='both', expand=True)

        # create data treeview
        self.treeview = ttk.Treeview(data_tab)
        self.treeview.place(relheight=1, relwidth=1)
        self.treescrollx = ttk.Scrollbar(data_tab, orient='horizontal', command=self.treeview.xview)
        self.treescrolly = ttk.Scrollbar(data_tab, orient='vertical', command=self.treeview.yview)
        self.treeview.configure(xscrollcommand=self.treescrollx.set, yscrollcommand=self.treescrolly.set)
        self.treescrollx.pack(side='bottom', fill='x')
        self.treescrolly.pack(side='right', fill='y')

        # threads
        # self.resize_thread = threading.Thread(target=self.resize_timer, name='Resize thread', daemon=True)
        # # self.resize_thread.start()

    def new_project(self):
        new_values = CreateProject().show()

        if new_values != None:
            self.values = new_values

            for file in self.values['files'].items():
                if file[0] == 'export':
                    continue
                self.values['files'][file[0]] = shutil.copy2(file[1], self.values['project'])
            self.values['files']['export'] = self.values['project'] + '/' + self.values['files']['export']
            
            print(json.dumps(self.values, indent=4))

            self.create_image()
            export_info = ExportInfo(self.values)
            self.dataset = export_info.get_data()

            if type(self.dataset) is not type(pd.DataFrame()):
                messagebox.showerror("Error", "Someting went wrong!")
            else:
                self.fill_treeview()
                self.create_heatmap()
                self.save()
                
                messagebox.showinfo("Export", "Succesfully created data!")          

    def open_project(self):
        file = filedialog.askopenfilename()
        file_handle = open(file)
        self.values = json.load(file_handle)
        self.dataset = pd.read_csv(self.values['files']['export'])

        self.create_image()
        self.create_heatmap()
        self.fill_treeview()

        for aoi in self.values['AOIs']:

            x, y, w, h = aoi['coords']
            name = aoi['name']

            r = 5
            id = self.canvas.create_rectangle(*aoi['coords'], outline='red', tags='all')
            close_id = self.canvas.create_oval(w-r, y-r, w+r, y+r, fill='grey', tags='all')

            text_id = self.canvas.create_text(x, y-10, anchor=W, text=name, fill='red', tags='all')
            self.aoi_list.append({'name': name, 'id': id, 'close': close_id, 'text': text_id})

    def save(self):

        if self.values != None:
            
            aoi_coords = []

            for aoi in self.aoi_list:
                aoi_coords.append({'name': aoi['name'],
                                   'coords': self.canvas.coords(aoi['id']),
                                   'close': self.canvas.coords(aoi['close'])})

            self.values['AOIs'] = aoi_coords
            json_values = json.dumps(self.values, indent=4)

            with open(f"{self.values['project']}/project.json", 'w') as f:
                f.write(json_values)
                f.close()

            messagebox.showinfo("Saving completed", "Success!")
        else:
            messagebox.showerror("Error saving", "No project opened.")

    def clear_treeview(self):
        self.treeview.delete(*self.treeview.get_children())

    def fill_treeview(self):
        self.clear_treeview()

        self.treeview['column'] = list(self.dataset.columns)
        self.treeview['show'] = 'headings'

        for column in self.treeview['columns']:
            self.treeview.heading(column, text=column)
        
        rows = self.dataset.head(1000).to_numpy().tolist()

        for row in rows:
            self.treeview.insert("", 'end', values=row)

    def canvas_click_handler(self, event):

        for aoi in self.aoi_list:

            x, y, w, h = self.canvas.coords(aoi['close'])
            center = ((x + w) / 2, (y + h) / 2)

            x = (event.x - center[0]) ** 2
            y = (event.y - center[1]) ** 2

            distance = math.sqrt(x+y)

            if distance < 6:
                self.canvas.delete(aoi['close'])
                self.canvas.delete(aoi['id'])
                self.canvas.delete(aoi['text'])
                self.aoi_list.remove(aoi)
                return

        self.line_start_x = event.x
        self.line_start_y = event.y
        self.drawing = True

    def draw_motion(self, event):

        if self.drawing:
            self.canvas.delete('temp_line_objects')
            self.canvas.create_rectangle(self.line_start_x, self.line_start_y, event.x, event.y, tags='temp_line_objects', outline='red')
        
    def canvas_click_release_handler(self, event):

        if self.drawing:
            self.canvas.delete('temp_line_objects')
            id = self.canvas.create_rectangle(self.line_start_x, self.line_start_y, event.x, event.y, outline='red', tags='all')
            name = simpledialog.askstring("Input", "AOI name?", parent=self)

            if name == None:
                self.canvas.delete(id)
            else:
                        
                x, y, w, h = self.canvas.coords(id)
                text_id = self.canvas.create_text(x, y-10, anchor=W, text=name, fill='red', tags='all')
                r = 5
                close_id = self.canvas.create_oval(w-r, y-r, w+r, y+r, fill='grey', tags='all')
                self.aoi_list.append({'name': name, 'id': id, 'close': close_id, 'text': text_id})
            
            self.drawing = False

    def create_image(self):
        self.img = Image.open(self.values['files']['panorama'])
        self.update_image()

    def create_heatmap(self):
        self.heatmap_maker = HeatmapMaker(self.values['files']['panorama'], data=self.dataset, filter=3)
        self.heatmap = Image.fromarray(self.heatmap_maker.make_heatmap())
        self.map_container = self.heatmap_canvas.create_image(0, 0, anchor=NW, image=ImageTk.PhotoImage(self.heatmap))
        self.update_heatmap()

    def update_image(self):
        self.res_img = self.img.resize((self.winfo_width(), self.winfo_height()))
        self.res_img = ImageTk.PhotoImage(image=self.res_img)
        self.canvas.itemconfig(self.container, image=self.res_img)

    def update_heatmap(self):
        self.res_map =  self.heatmap.resize((self.winfo_width(), self.winfo_height()))
        self.res_map = ImageTk.PhotoImage(image=self.res_map)
        self.heatmap_canvas.itemconfig(self.map_container, image = self.res_map)


if __name__ == "__main__":
    app = MainWindow()
    app.mainloop()