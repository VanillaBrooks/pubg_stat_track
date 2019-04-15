import subprocess
import os
import time

# current working dir (where the folder is )
dir_path = os.path.dirname(os.path.realpath(__file__))

# start a command prompt instance
subprocess.Popen("git pull",
                         shell=True,
                         stdin=subprocess.PIPE,
                         cwd=dir_path)
time.sleep(5)
subprocess.Popen("python setup.py install",
                 shell=True,
                 stdin=subprocess.PIPE,
                 cwd=dir_path)

print("sleeping for 10 seconds while changes are pulled")
time.sleep(2)
print("starting the bot")

import src
