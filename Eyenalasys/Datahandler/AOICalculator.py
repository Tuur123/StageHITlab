import numpy as np
import pandas as pd

class AOICalculator:

    def __init__(self, canvas_obj) -> None:
        
        # global vars
        self.visit_count = []
        self.time_spent = []
        self.fixations = []
        self.pupil_sizes = []
        self.movement_types = []

        # internal vars
        self.__aoi_list = []
        self.__canvas = canvas_obj
        self.__dataset = None
        self.__coords = None

        # vars used per AoI
        self.__visits = None
        self.__aoi_points = None

    @property
    def coords(self):
        return self.__coords

    @coords.setter
    def coords(self, new_coords):
        self.__coords = new_coords

    @property
    def dataset(self):
        return self.__dataset

    @dataset.setter
    def dataset(self, new_dataset):
        self.__dataset = new_dataset

        if self.__dataset is not None:

            self.__dataset['S_DOWN_X'] = self.__dataset['X'].shift(1)
            self.__dataset['S_UP_X'] = self.__dataset['X'].shift(-1)
            self.__dataset['S_DOWN_Y'] = self.__dataset['X'].shift(1)
            self.__dataset['S_UP_Y'] = self.__dataset['Y'].shift(-1)

            self.__dataset.sort_values('world_index')

    @property
    def aoi_list(self):
        return self.__aoi_list

    @aoi_list.setter
    def aoi_list(self, new_list):
        
        # if len(self.__aoi_list) ==  0 and len(new_list) > 0:
        self.__aoi_list = new_list

        for aoi in self.__aoi_list:
            self.__calc_globals(aoi)

        # # get difference with new list, do we need to recalculate or not?
        # if len(self.__aoi_list) < len(new_list):

        #     # new AoI
        #     self.__calc_globals(new_list[-1])
        
        # if len(self.__aoi_list) > len(new_list):

        #     # Aoi deleted, keep new_list
        #     s = set(new_list)
        #     deleted_AoIs = [x for x in self.__aoi_list if x not in s]
        #     self.__aoi_list.remove(deleted_AoIs)

    # returns list of all AoI's with their datapoints
    def __calc_globals(self, aoi):
        
        if self.__coords == None:
            return

        x1, y1, w, h = self.__canvas.coords(aoi['id'])
        world_coords, res_coords = self.coords
        
        

        x2, y2 = x1+w, y1+h

        in_aoi = (x1 < self.__dataset['X']) & (self.__dataset['X'] < x2) & (y1 < self.__dataset['Y']) & (self.__dataset['Y'] < y2)
        enter_aoi = in_aoi & ~((x1 < self.__dataset['S_DOWN_X']) & (self.__dataset['S_DOWN_X'] < x2) & (y1 < self.__dataset['S_DOWN_Y']) & (self.__dataset['S_DOWN_Y'] < y2))
        exit_aoi = in_aoi & ~((x1 < self.__dataset['S_UP_X']) & (self.__dataset['S_UP_X'] < x2) & (y1 < self.__dataset['S_UP_Y']) & (self.__dataset['S_UP_Y'] < y2))

        aoi_dataset = self.__dataset

        aoi_dataset['ENTER'] = enter_aoi
        aoi_dataset['IN'] = in_aoi
        aoi_dataset['EXIT'] = exit_aoi

        self.__aoi_points = aoi_dataset.drop(aoi_dataset[(aoi_dataset['ENTER'] == False) & (aoi_dataset['IN'] == False) & (aoi_dataset['EXIT'] == False)].index)

        self.__calculate()

    def __calculate(self):

        self.__calc_visits()
        self.__calc_time_spent()
        self.__calc_fixations()
        self.__calc_pupil_size()
        self.__calc_movement_types()

        for i in range(len(self.visit_count)):
            print(self.visit_count[i])
            print(self.time_spent[i])
            print(self.fixations[i])
            print(self.pupil_sizes[i])
            print(self.movement_types[i])

    # calculates a list of visits
    def __calc_visits(self):

        visits = []
        collecting = False

        for index, row in self.__aoi_points.iterrows():
            
            if not collecting:
                tmp_visit = []

            if row['ENTER'] == True and row['EXIT'] == False:
                tmp_visit.append(row)
                collecting = True

            if collecting == True and row['IN'] == True:
                tmp_visit.append(row)

            if row['ENTER'] == False and row['EXIT'] == True:
                tmp_visit = pd.DataFrame(tmp_visit)
                if len(tmp_visit) == 0:
                    collecting = False
                    continue

                if 'Fixation' in tmp_visit['Eye movement type'].unique():
                    visits.append(tmp_visit)
                collecting = False
        
        self.__visits = visits
        self.visit_count.append(len(visits))

    # calculates total time spent in AoI visit and time spent each visit
    def __calc_time_spent(self):
        
        time_spent_dict = dict()

        total = 0
        for idx, visit in enumerate(self.__visits):

            start_time = visit['Recording timestamp'][0]
            end_time = visit['Recording timestamp'][-1]

            duration = end_time - start_time

            time_spent_dict[idx] = duration
            total += duration
        
        time_spent_dict['total'] = total

        self.time_spent.append(time_spent_dict)

    # calculates all fixations
    def __calc_fixations(self):
        
        fixation_dict = dict()
        total = 0

        for idx, visit in enumerate(self.__visits):

            fixations = visit[visit['Eye movement type'] == 'Fixation']

            fixation_dict[idx] = fixations
            total += len(fixations)

        self.fixations.append(fixation_dict)

    # calculates avg pupil sizes for l en r and change in pupil size
    def __calc_pupil_size(self):
        
        pupil_dict = dict()

        pupil_list_l = []
        pupil_list_r = []
        timestamps_list = []

        for idx, visit in enumerate(self.__visits):

            pupil_l = visit['Pupil diameter left']
            pupil_r = visit['Pupil diameter right']
            timestamps = visit['Recording time']

            pupil_list_l.append(pupil_l)
            pupil_list_r.append(pupil_r)
            timestamps_list.append(timestamps)

            l_avg = np.average(pupil_l)
            r_avg = np.average(pupil_r)

            l_diff = np.diff(pupil_l) / np.diff(timestamps)
            r_diff = np.diff(pupil_r) / np.diff(timestamps)

            pupil_dict[idx] = {'l_avg': l_avg, 'r_avg': r_avg, 'l_diff': l_diff, 'r_diff': r_diff}

        l_avg_total = np.average(pupil_list_l)
        r_avg_total = np.average(pupil_list_r)

        l_diff_total = np.diff(pupil_list_l) / np.diff(timestamps_list)
        r_diff_total = np.diff(pupil_list_r) / np.diff(timestamps_list)   

        pupil_dict['total'] = {'l_avg': l_avg_total, 'r_avg': r_avg_total, 'l_diff': l_diff_total, 'r_diff': r_diff_total}

        self.pupil_sizes.append(pupil_dict)

    # calculates countmatrix of movement types in AoI
    def __calc_movement_types(self):

        movement_dict = dict()
        total = 0

        if len(self.__visits) == 0:
            self.movement_types.append(movement_dict)
            return

        for idx, visit in enumerate(self.__visits):

            unique, counts = np.unique(visit['Eye movement type'], return_counts=True)
            movement_dict[idx] = dict(zip(unique, counts))

            total = np.add(total, counts)
        
        movement_dict['total'] = dict(zip(unique, counts))

        self.movement_types.append(movement_dict)