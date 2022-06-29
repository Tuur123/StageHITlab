# Imports
import time
from datetime import timezone
import datetime
from pylsl import StreamOutlet, StreamInfo, cf_string
from threading import Thread
import PySimpleGUI as Gui
import numpy as np

# Define a stream:
# Name = The folder where the data will be saved
# Type = The name of the file and the type of data you are streaming
# channel_count = the amount of data elements you are sending
# channel_format = type of data you are streaming
str_info = StreamInfo(name='Root', type='data_stream', channel_count=5, channel_format=cf_string)

# Define what data you are streaming in the channels
# In this case we are sending an id a type and a location
channel_names = ['ID', 'classType', 'x', 'y', 'z']
channels = str_info.desc().append_child("channels")
for name in channel_names:
    channels.append_child('channel').append_child_value("label", name)

# Actually create the stream from the info
outlet = StreamOutlet(str_info)

# A quick GUI (can be ignored is just for demo)
Gui.theme('DarkAmber')
layout = [[
    Gui.Text('Send data:'),
    Gui.Button('Start', key=0),
    Gui.Button('Stop', key=1, disabled=True)
]]
window = Gui.Window('Setup', layout)
sending_data = False
thread_running = False
data_thread = None

nr_of_objects = 10
obj_classes = ['Table', 'Box']


def send_data():
    global sending_data, nr_of_objects, obj_classes
    time_start = datetime.datetime.now()
    while sending_data:
        # slight delay to prevent buffers from overloading
        time.sleep(0.02)

        # Getting the current date and time
        dt = datetime.datetime.now(timezone.utc)
        utc_time = dt.replace(tzinfo=timezone.utc)
        utc_timestamp = utc_time.timestamp()
        delta_time = time_start - datetime.datetime.now()

        # Create objects
        data = [[], [], [], [], []]
        for i in range(nr_of_objects):
            # Calculate data
            obj_id = i
            obj_type = obj_classes[i % len(obj_classes)]
            x = np.cos(delta_time.total_seconds() / 2) * 100 + 100 * i
            y = 0
            z = np.sin(delta_time.total_seconds()) * 50 + 200

            data[0].append(str(obj_id))
            data[1].append(obj_type)
            data[2].append(str(x))
            data[3].append(str(y))
            data[4].append(str(z))

        # Send data
        # Time as a UTC timestamp
        # Data as an array of the selected type, this case a string
        outlet.push_sample(
            timestamp=utc_timestamp,
            x=[str(data[0]),
               str(data[1]),
               str(data[2]),
               str(data[3]),
               str(data[4])]
        )


# Logic of the window, when to send and stop sending data
while not window.was_closed():
    event, values = window.read()

    if event == 0:
        sending_data = True
        window[0].Update(disabled=True)
        window[1].Update(disabled=False)
        if data_thread is None:
            data_thread = Thread(target=send_data)
    if event == 1:
        sending_data = False
        window[0].Update(disabled=False)
        window[1].Update(disabled=True)
        if data_thread:
            data_thread.join()
            thread_running = False
            data_thread = None

    if sending_data and not thread_running:
        if data_thread:
            thread_running = True
            data_thread.start()

sending_data = False
if data_thread:
    data_thread.join()
    thread_running = False
