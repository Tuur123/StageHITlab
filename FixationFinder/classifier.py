import pickle
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

            # eye_data = samples[35:38] + samples[45:48]
            eye_data = samples

            current_samples.append(list(map(float, eye_data)))
            current_timestamps.append(float(timestamp))

        else:
            
            gaze_dir_left_x = current_samples[1][0]
            gaze_dir_left_y = current_samples[1][1]
            gaze_dir_left_z = current_samples[1][2]

            gaze_dir_right_x = current_samples[1][3]
            gaze_dir_right_y = current_samples[1][4]
            gaze_dir_right_z = current_samples[1][5]

            gaze_dir_left_x_next = current_samples[0][0]
            gaze_dir_left_y_next = current_samples[0][1]
            gaze_dir_left_z_next = current_samples[0][2]

            gaze_dir_right_x_next = current_samples[0][3]
            gaze_dir_right_y_next = current_samples[0][4]
            gaze_dir_right_z_next = current_samples[0][5]

            gaze_dir_avg_x = (gaze_dir_left_x + gaze_dir_right_x) * 0.5
            gaze_dir_avg_y = (gaze_dir_left_y + gaze_dir_right_y) * 0.5
            gaze_dir_avg_z = (gaze_dir_left_z + gaze_dir_right_z) * 0.5

            gaze_dir_avg_x_next = (gaze_dir_left_x_next + gaze_dir_right_x_next) * 0.5
            gaze_dir_avg_y_next = (gaze_dir_left_y_next + gaze_dir_right_y_next) * 0.5
            gaze_dir_avg_z_next = (gaze_dir_left_z_next + gaze_dir_right_z_next) * 0.5


            # arccos[(xa * xb + ya * yb + za * zb) / (√(xa2 + ya2 + za2) * √(xb2 + yb2 + zb2))]

            angle = np.arccos((gaze_dir_avg_x * gaze_dir_avg_x_next + gaze_dir_avg_y * gaze_dir_avg_y_next + gaze_dir_avg_z * gaze_dir_avg_y_next) \
            / (np.sqrt(gaze_dir_avg_x ** 2 + gaze_dir_avg_y ** 2 + gaze_dir_avg_z ** 2) * np.sqrt(gaze_dir_avg_x_next ** 2 + gaze_dir_avg_y_next ** 2 + gaze_dir_avg_y_next ** 2)))

            time_diff = current_timestamps[1] - current_timestamps[0]

            velocity = angle / (time_diff / 1000)
            
            if velocity > 0.10:
                print(f"Saccade, velocity: {round(velocity)} °/s, angle {round(angle, 2)}")
                outlet.push_sample(['Saccade'], timestamp=current_timestamps[0])
            else:
                print(f"Fixatie, velocity: {round(velocity)} °/s, angle {round(angle, 2)}")
                outlet.push_sample(['Fixatie'], timestamp=current_timestamps[0])

            velocities.append([velocity, current_timestamps[0]])
        
            current_samples = []
            current_timestamps = []

except KeyboardInterrupt:
    print("Closing...")

finally:
    with open('velocities.pkl', 'wb') as f:
        pickle.dump(velocities, f)