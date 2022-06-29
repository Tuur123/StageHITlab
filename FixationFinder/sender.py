import time
import pandas as pd
from pylsl import StreamInfo, StreamOutlet, cf_string

data = pd.read_csv('FixationFinder\data.tsv', sep='\t')
data = data[['Gaze direction right X',
             'Gaze direction right Y',
             'Gaze direction right Z',
             'Gaze direction left X',
             'Gaze direction left Y',
             'Gaze direction left Z',
             'Computer timestamp']]

data.dropna(inplace=True)
data['Computer timestamp'] = data['Computer timestamp'] / 1000
data = data.applymap(str)
data['Computer timestamp'] = data['Computer timestamp'].astype(float)

str_info = StreamInfo(name='Root', type='eye', channel_count=6, channel_format=cf_string)

channel_names = ['Gaze direction right X', 'Gaze direction right Y', 'Gaze direction right Z', 'Gaze direction left X', 'Gaze direction left Y', 'Gaze direction left Z']
channels = str_info.desc().append_child("channels")
for name in channel_names:
    channels.append_child('channel').append_child_value("label", name)

# next make an outlet
outlet = StreamOutlet(str_info)

print("now sending data...")

for row in data.iterrows():

    sample = row[1].tolist()

    # now send it and wait for a bit
    outlet.push_sample(sample[:-1], timestamp=sample[-1])
    # print(sample)
    time.sleep(0.01)