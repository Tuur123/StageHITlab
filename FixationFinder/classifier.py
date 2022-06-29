import pickle
import time
import numpy as np
from pylsl import StreamInlet, resolve_stream, StreamInfo, StreamOutlet, cf_string

print("looking for a stream...")

streams = resolve_stream('type', 'eye')

# create a new inlet to read from the stream
inlet = StreamInlet(streams[0])

str_info = StreamInfo(name='Eye_root', type='eye_movement', channel_count=1, channel_format=cf_string)

channel_names = ['Eye movement type']
channels = str_info.desc().append_child("channels")
for name in channel_names:
    channels.append_child('channel').append_child_value("label", name)

# next make an outlet
outlet = StreamOutlet(str_info)

current_samples = []
current_timestamps = []
velocities = []


try:
    while True:

        if len(current_samples) <= 2:

            samples, timestamp = inlet.pull_sample()
            current_samples.append(list(map(float, samples)))
            current_timestamps.append(float(timestamp))

        else:
            
            gaze_dir_avg_x = (current_samples[0][0] + current_samples[0][3]) / 2
            gaze_dir_avg_y = (current_samples[0][1] + current_samples[0][4]) / 2
            gaze_dir_avg_z = (current_samples[0][2] + current_samples[0][5]) / 2

            gaze_dir_avg_x_next = (current_samples[1][0] + current_samples[1][3]) / 2
            gaze_dir_avg_y_next = (current_samples[1][1] + current_samples[1][4]) / 2
            gaze_dir_avg_y_next = (current_samples[1][2] + current_samples[1][5]) / 2

            # arccos[(xa * xb + ya * yb + za * zb) / (√(xa2 + ya2 + za2) * √(xb2 + yb2 + zb2))]

            angle = np.arccos((gaze_dir_avg_x * gaze_dir_avg_x_next + gaze_dir_avg_y * gaze_dir_avg_y_next + gaze_dir_avg_z * gaze_dir_avg_y_next) \
            / (np.sqrt(gaze_dir_avg_x ** 2 + gaze_dir_avg_y ** 2 + gaze_dir_avg_z ** 2) * np.sqrt(gaze_dir_avg_x_next ** 2 + gaze_dir_avg_y_next ** 2 + gaze_dir_avg_y_next ** 2)))

            time_diff = current_timestamps[1] - current_timestamps[0]

            velocity = angle / time_diff
            
            if velocity > 0.8:
                print(f"Saccade, velocity: {velocity}")
                outlet.push_sample(['Saccade'], timestamp=time.time())
            else:
                print(f"Fixatie, velocity: {velocity}")
                outlet.push_sample(['Fixatie'], timestamp=time.time())

            velocities.append(velocity)
        
            current_samples = []
            current_timestamps = []

except KeyboardInterrupt:
    print("Closing...")
    
finally:
    with open('velocities.pkl', 'wb') as f:
        pickle.dump(velocities, f)