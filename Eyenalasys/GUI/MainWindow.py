import os
import json

import tkinter as tk
from tkinter import *
from tkinter import ttk
from tkinter import messagebox, filedialog
from PIL import ImageTk, Image

from Export import Export
from CreateProject import CreateProject


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



    def new_project(self):
        new_values = CreateProject().show()

        if new_values != None:
            self.values = new_values
            print(self.values)
            self.create_image()

            self.dataset = Export(self.values['data'], self.values['video'], self.values['tracker'], self.values['panorama']).show()

    def open_project(self):
        file = filedialog.askopenfilename()
        file_handle = open(file)
        self.values = json.load(file_handle)

        self.create_image()

    def save(self):

        if self.values != None:
            json_values = json.dumps(self.values, indent=4)

            with open('project.json', 'w') as f:
                f.write(json_values)
                f.close()

            messagebox.showinfo("Saving completed", "Success!")
        else:
            messagebox.showerror("Error saving", "No project opened.")

    def on_resize(self, event):
        if self.values != None:
            self.update_image()

    def create_image(self):
        self.img = Image.open(self.values['panorama'])
        self.update_image()

    def update_image(self):
        self.res_img = self.img.resize((self.winfo_width(), self.winfo_height()))
        self.res_img = ImageTk.PhotoImage(image=self.res_img)
        self.canvas.itemconfig(self.container, image=self.res_img)

if __name__ == "__main__":
    app = MainWindow()
    app.mainloop()