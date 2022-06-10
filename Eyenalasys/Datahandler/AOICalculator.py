import numpy as np
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt

class AOICalculator:

    def __init__(self, canvas_obj, plotter) -> None:
        
        # internal vars
        self.__aoi_list = []
        self.__canvas = canvas_obj
        self.__dataset = None
        self.__plotter = plotter

    def set_data(self, rescaled_coords, original_coords, dataset):

        original_width, original_height = original_coords

        dataset = dataset[dataset['X'] >= 0]
        dataset = dataset[dataset['Y'] >= 0]
        dataset = dataset[dataset['X'] <= original_width]
        dataset = dataset[dataset['Y'] <= original_height]

        interval_min = 0
        interval_max_x, interval_max_y = rescaled_coords

        dataset['X'] = (dataset['X'] - np.min(dataset['X'])) / (np.max(dataset['X']) - np.min(dataset['X'])) * (interval_max_x - interval_min) + interval_min
        dataset['Y'] = (dataset['Y'] - np.min(dataset['Y'])) / (np.max(dataset['Y']) - np.min(dataset['Y'])) * (interval_max_y - interval_min) + interval_min

        self.__dataset = dataset

    @property
    def aoi_list(self):
        return self.__aoi_list

    @aoi_list.setter
    def aoi_list(self, new_list):
        
        if len(new_list) != None:
            self.__aoi_list = new_list

            data = []
            
            for aoi_idx, aoi in enumerate(self.__aoi_list):
                data.append(self.__calculate(aoi, aoi_idx))

            self.__plotter.data = data

    def __calculate(self, aoi, aoi_idx):
        
        x1, y1, w, h = self.__canvas.coords(aoi['id'])

        x2, y2 = x1+w, y1+h

        in_aoi = (x1 <= self.__dataset['X']) & (self.__dataset['X'] <= x2) & (y1 <= self.__dataset['Y']) & (self.__dataset['Y'] <= y2)

        aoi_dataset = self.__dataset
        aoi_dataset['IN'] = in_aoi

        visits = self.__calc_visits(aoi_dataset)

        aoi_data = pd.DataFrame()


        # calculates total time spent in AoI visit and time spent each visit
        for visit_idx, visit in enumerate(visits):

            start_time = visit['Recording timestamp'].values[0]
            end_time = visit['Recording timestamp'].values[-1]

            duration = end_time - start_time

            aoi_data.loc[visit_idx, 'dwell_time'] = duration
            aoi_data.loc[visit_idx, 'visit_start'] = start_time
            aoi_data.loc[visit_idx, 'visit_end'] = end_time
        
            duration = 0

            for row_idx, row in visit.iterrows():

                if row['Eye movement type'] == 'Fixation':
                    duration += row['Gaze event duration']

            aoi_data.loc[visit_idx, 'total_fixation_time'] = duration / 1000


            # calculates avg pupil sizes for l en r and change in pupil size
            pupil_list_l = []
            pupil_list_r = []
            timestamps_list = []

            pupil_visit = visit.dropna(subset=['Pupil diameter left', 'Pupil diameter right'])
            pupil_l = pupil_visit['Pupil diameter left']
            pupil_r = pupil_visit['Pupil diameter right']
            timestamps = pupil_visit['Recording timestamp'] / 1000

            if len(pupil_l) != 0 and len(pupil_r) != 0:

                pupil_list_l.append(pupil_l)
                pupil_list_r.append(pupil_r)
                timestamps_list.append(timestamps)

                l_avg = np.average(pupil_l)
                r_avg = np.average(pupil_r)

                l_diff = np.average(np.diff(pupil_l) / np.diff(timestamps))
                r_diff = np.average(np.diff(pupil_r) / np.diff(timestamps))

                avg = np.average(l_avg + r_avg)
                diff = np.average(l_diff + r_diff)

                aoi_data.loc[visit_idx, 'pupil_dia_avg'] = avg
                aoi_data.loc[visit_idx, 'pupil_dia_diff'] = diff


            # calculates movement types in AoI
            types = []

            unique, counts = np.unique(visit['Eye movement type'], return_counts=True)
            
            for type, count in zip(unique, counts):
                aoi_data.loc[visit_idx, type + 's'] = count

                if type not in types:
                    types.append(type + 's')
            
            for type in types:
                aoi_data[type].fillna(0, inplace=True)

        return (aoi['name'], aoi_data)

    # calculates a list of visits
    def __calc_visits(self, aoi_dataset):

        visits = []
        tmp_visits = []
        collecting = False

        # idx moet erbij
        for index, row in aoi_dataset.iterrows():
            
            if row['IN'] == True and row['Eye movement type'] == 'Saccade':
                tmp_visits.append(row)
                collecting = True

            elif row['IN'] == True and collecting:
                tmp_visits.append(row)

            else:
                tmp_visits = pd.DataFrame(tmp_visits)
                if len(tmp_visits) > 5:

                    if 'Fixation' in tmp_visits['Eye movement type'].unique():
                        visits.append(tmp_visits)

                tmp_visits = []
                collecting = False
        
        return visits