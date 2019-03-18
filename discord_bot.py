# outside libraries
import discord
import requests

# std lib
import os
import time
import asyncio
import logging
import datetime

# local files
from api import discord_token


# ['kills', 'damageDealt', 'revives']


class MyClient(discord.Client):

    async def on_ready(self):
        pass
    async def on_message(self, message):
        if 'stuff' in message.content:
            # do stuff
            pass


    async def send_the_file(self,message, file_name):
        await client.send_file(message.channel, file_name)

        # for channel in client.get_all_channels():
        #     if 'cat' in channel.name:
        #         logging.info(f'Sending file to channel: {channel}')
        #         await client.send_file(channel, self.file)
        #         # send_message

# construct line graph and send to discord chat
async def construct_graph():
    pass

# send out the stats to a discord channel
async def send_stats():
    pass

# sets up all logging config and logging folders
def logger_config():
    logging_folder = 'logging/'
    try:
        os.mkdir(logging_folder)
    except Exception:
        pass

    # month - day __ hour - minute - second
    LOG_FILENAME = logging_folder + \
        datetime.datetime.now().strftime('%m-%d__%H-%M-%S') + '.txt'

    logging.basicConfig(filename=LOG_FILENAME,
                        level=logging.INFO,
                        format='%(asctime)s.%(msecs)03d %(levelname)s %(module)s - %(funcName)s: %(message)s',
                        datefmt='%Y-%m-%d %H:%M:%S')


if __name__ == '__main__':
    logger_config()
    client = MyClient()
    client.run(discord_token)
