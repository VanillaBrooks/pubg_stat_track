import subprocess
import os
import time

# current working dir (where the folder is )
dir_path = os.path.dirname(os.path.realpath(__file__))

# start a command prompt instance
shell = subprocess.Popen("git pull",
                         shell=True,
                         stdin=subprocess.PIPE,
                         cwd=dir_path)

print("sleeping for 10 seconds while changes are pulled")
time.sleep(10)
print("starting the bot")

import src
