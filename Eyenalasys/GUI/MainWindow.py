import json
import shutil
import pandas as pd

import tkinter as tk
from tkinter import *
from tkinter import ttk
from tkinter import messagebox, filedialog
from PIL import ImageTk, Image

from GUI.Export import ExportInfo
from GUI.CreateProject import CreateProject


class MainWindow(tk.Tk):

    def __init__(self):
        super().__init__()

        # bind resize event
        self.bind("<Configure>", self.on_resize)
        
        # set values to None
        self.values = None
        self.dataset = None

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
        tab_control.add(pan_tab, text='Panorama')
        tab_control.add(data_tab, text='Data')
        tab_control.pack(fill='both', expand=True)

        # create img container
        self.img = ImageTk.PhotoImage(file='./assets/placeholder.png')
        self.canvas = Canvas(pan_tab)
        self.canvas.pack(fill='both', expand=True)
        self.container = self.canvas.create_image(0, 0, anchor=NW, image=self.img)

        # create data treeview
        self.treeview = ttk.Treeview(data_tab)
        self.treeview.place(relheight=1, relwidth=1)

        self.treescrollx = ttk.Scrollbar(data_tab, orient='horizontal', command=self.treeview.xview)
        self.treescrolly = ttk.Scrollbar(data_tab, orient='vertical', command=self.treeview.yview)

        self.treeview.configure(xscrollcommand=self.treescrollx.set, yscrollcommand=self.treescrolly.set)

        self.treescrollx.pack(side='bottom', fill='x')
        self.treescrolly.pack(side='right', fill='y')

    def new_project(self):
        new_values = CreateProject().show()

        if new_values != None:
            self.values = new_values

            for file in self.values['files'].items():
                if file[0] == 'export':
                    break
                self.values['files'][file[0]] = shutil.copy2(file[1], self.values['project'])

            print(json.dumps(self.values, indent=4))

            self.create_image()
            export_info = ExportInfo(self.values)
            self.dataset = export_info.get_data()

            if type(self.dataset) is not type(pd.DataFrame()):
                messagebox.showerror("Error", "Someting went wrong!")
            else:
                self.save()
                self.fill_treeview()
                messagebox.showinfo("Export", "Succesfully created data!")              

    def open_project(self):
        file = filedialog.askopenfilename()
        file_handle = open(file)
        self.values = json.load(file_handle)
        self.dataset = pd.read_csv(self.values['export'])

        print(self.values)

        self.create_image()
        self.fill_treeview()

    def save(self):

        if self.values != None:
            json_values = json.dumps(self.values, indent=4)

            with open(self.values['project'] + 'project.json', 'w') as f:
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

    def on_resize(self, event):
        if self.values != None:
            self.update_image()

    def create_image(self):
        self.img = Image.open(self.values['files']['panorama'])
        self.update_image()

    def update_image(self):
        self.res_img = self.img.resize((self.winfo_width(), self.winfo_height()))
        self.res_img = ImageTk.PhotoImage(image=self.res_img)
        self.canvas.itemconfig(self.container, image=self.res_img)

if __name__ == "__main__":
    app = MainWindow()
    app.mainloop()
