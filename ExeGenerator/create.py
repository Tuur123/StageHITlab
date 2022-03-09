import subprocess
import sys
import os
import configparser
import json

files = []
hooks = []
script_location = None


config_file = 'config.ini'
if len(sys.argv) > 1:
    config_file = sys.argv[1]

config = configparser.ConfigParser()
config.read(config_file)


try:
    files = json.loads(config['DEFAULT']['files'])
    hooks = json.loads(config['DEFAULT']['hooks'])
    script_location = config['DEFAULT']['script']
except Exception as e:
    print(f"Parameter {e} not found.")
    exit(1)

file_command = ""
for filepath in files:

    dir = os.path.dirname(filepath)
    file = os.path.basename(filepath)

    if not file:
        file = '.'

    file_command += f" --add-data '{dir};{file}'"

full_command = f"pyinstaller --noconfirm --onefile --windowed --debug all{file_command} --additional-hooks-dir={hooks} {script_location}"

subprocess.call(full_command)