import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import numpy as np


import tkinter as tk
from tkinter import ttk
import matplotlib

matplotlib.use('TkAgg')

from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import  FigureCanvasTkAgg,  NavigationToolbar2Tk

from GUI.ScrollFrame import VerticalScrolledFrame

class Plotter:

    def __init__(self, tab_control) -> None:
        
        self.__tab_control = tab_control
        self.__aoi_data = []
        self.__aoi_tabs = []

    @property
    def data(self):
        return self.__data

    @data.setter
    def data(self, new_data):

        self.__aoi_data = new_data

        max_length = 0

        for data in self.__aoi_data:
            if len(data[1]) > max_length:
                max_length = len(data[1])
        
        for tab in self.__aoi_tabs:
            tab.destroy()


        plot_width = max_length // 3
        plot_height = len(self.__aoi_data) * 10

        for metric in ['Dwell Time', 'Fixation Length', 'Pupil Sizes', 'Pupil Speeds', 'Movement types']:

            metric_tab = VerticalScrolledFrame(self.__tab_control)
            self.__aoi_tabs.append(metric_tab)
            self.__tab_control.add(metric_tab, text=metric)
            self.__tab_control.pack(fill='both', expand=True)

            figure = Figure(figsize=(plot_width, plot_height))

            # create FigureCanvasTkAgg object
            figure_canvas = FigureCanvasTkAgg(figure, metric_tab.interior)

            # create the toolbar
            NavigationToolbar2Tk(figure_canvas, metric_tab.interior)

            if metric == 'Dwell Time':


                figure.suptitle('Dwell Time', fontsize = plot_width)
                figure.subplots_adjust(hspace=0.3)

                for n, aoi in enumerate(self.__aoi_data):
                    
                    if len(aoi[1]) != 0:
                        # add a new subplot iteratively
                        ax = figure.add_subplot(len(self.__aoi_data), 1, n + 1)
                        sns.barplot(data=aoi[1], y='dwell_time', x='visit_start', ci=None, ax=ax)
                        ax.set_xticklabels(ax.get_xticklabels(), rotation = 45, size = plot_width // 3)
                        ax.set(xlabel='seconds')
                        ax.set(ylabel='seconds')                    
                        ax.set_title(f'AoI {aoi[0]}', fontsize=plot_height)

            if metric == 'Fixation Length':

                figure.suptitle('Fixation Length', fontsize = plot_width)
                figure.subplots_adjust(hspace=0.3)

                for n, aoi in enumerate(self.__aoi_data):

                    if len(aoi[1]) != 0:
                        # add a new subplot iteratively
                        ax = figure.add_subplot(len(self.__aoi_data), 1, n + 1)
                        sns.barplot(data=aoi[1], y='total_fixation_time', x='visit_start', ci=None, ax=ax)
                        ax.set_xticklabels(ax.get_xticklabels(), rotation = 45, size = plot_width // 3)
                        ax.set(xlabel='seconds')
                        ax.set(ylabel='seconds')
                        ax.set_title(f'AoI {aoi[0]}', fontsize=plot_height)

            if metric == 'Pupil Sizes':

                figure.suptitle('Pupil Sizes', fontsize = plot_width)
                figure.subplots_adjust(hspace=0.3)

                for n, aoi in enumerate(self.__aoi_data):


                    if len(aoi[1]) != 0:
                        # add a new subplot iteratively
                        ax = figure.add_subplot(len(self.__aoi_data), 1, n + 1)
                        sns.barplot(data=aoi[1], y='pupil_dia_avg', x='visit_start', ci=None, ax=ax)
                        ax.set_xticklabels(ax.get_xticklabels(), rotation = 45, size = plot_width // 3)
                        ax.set(xlabel='seconds')
                        ax.set(ylabel='millimeter')
                        ax.set_title(f'AoI {aoi[0]}', fontsize=plot_height)

            if metric == 'Pupil Speeds':

                
                figure.suptitle('Pupil Speeds', fontsize = plot_width)
                figure.subplots_adjust(hspace=0.3)

                for n, aoi in enumerate(self.__aoi_data):

                    if len(aoi[1]) != 0:

                        # add a new subplot iteratively
                        ax = figure.add_subplot(len(self.__aoi_data), 1, n + 1)
                        sns.barplot(data=aoi[1], y='pupil_dia_diff', x='visit_start', ci=None, ax=ax)
                        ax.set_xticklabels(ax.get_xticklabels(), rotation = 45, size = plot_width // 3)
                        ax.set(xlabel='seconds')
                        ax.set(ylabel='millimeter per seconds')
                        ax.set_title(f'AoI {aoi[0]}', fontsize=plot_height)

            if metric == 'Movement types':

                
                figure.suptitle('Movement types', fontsize = plot_width)
                figure.subplots_adjust(hspace=0.3)

                for n, aoi in enumerate(self.__aoi_data):

                    if len(aoi[1]) != 0:
                        # add a new subplot iteratively
                        ax = figure.add_subplot(len(self.__aoi_data), 1, n + 1)
                        data = pd.melt(aoi[1], id_vars='visit_start', var_name="movement_type", value_name='count', value_vars=['Fixations', 'Saccades', 'Unclassifieds'])
                        sns.barplot(data=data, x='visit_start', y='count', hue='movement_type', ci=None, ax=ax)
                        ax.set_xticklabels(ax.get_xticklabels(), rotation = 45, size = plot_width // 3)
                        ax.set(xlabel='seconds')
                        ax.set(ylabel='movement type count')
                        ax.set_title(f'AoI {aoi[0]}', fontsize=plot_height)

            figure_canvas.draw()
            figure_canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=1)