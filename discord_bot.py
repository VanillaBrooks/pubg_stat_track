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
import pubg_api

# fields of the stats that we care about
stats_fields = ['kills', 'damageDealt', 'revives']

# conversion from discord name to pubg username
discord_to_pubg = {
    'Big Dick Bandit#8045': 'Loko_Soko',
    'Gigolojoe#7817': 'TheGigoloJoe',
    'PocPoc#7403': 'Poc_Poc',
    'Pool Boy Steve#7324': 'SandyBrooks',
    'colbykarlik#0348':'Captain_Crabby',
    'LEGIQn#7532':'LEGIQn_',
    'Joeyeyey#8697' : 'Joeyeyey',
    'happypenguin#9475': 'Happy--Penguin'
}

class MyClient(discord.Client):

    async def on_ready(self):
        print(f'ready {self.user}')

    async def on_message(self, message):
        
        if '?pubg' in message.content:
            if "stats" in message.content:
                print(f'query from {message.author}')
                strs = message.content.split(' ')

                hours = 10
                for item in strs:
                    if item.isdigit():
                        hours = int(item)
                current_time_utc = datetime.datetime.utcnow()
                query_time = current_time_utc - datetime.timedelta(hours=hours)

                pubg_user_list = await self.construct_user_list(message.author)

                rosters = await pubg_api.get_relevant_rosters(pubg_user_list, query_time)
                data = await pubg_api.parse_roster_stats(pubg_user_list, stats_fields, rosters)

                # send the data off

            elif "graph" in message.content:
                pass

            else:
                pass
                # send help on stuff
    async def construct_user_list(self, author):
        channels = client.get_all_channels()
        users = []
        author = str(author)

        # cycle through all channels
        for channel in channels:
            # convert to strings for simplicity
            channel_users = [str(i) for i in channel.voice_members]

            # if the query comes from that channel the team
            # must be playing in that channel
            if author in channel_users:

                for member in channel.voice_members:
                    mem_str = str(member)

                    # if the persons name has a pubg username
                    # then we fetch it and add it to final list
                    if mem_str in discord_to_pubg:
                        users.append(discord_to_pubg[mem_str])

        return users
                
    
    async def send_the_file(self,message, file_name):
        await client.send_file(message.channel, file_name)


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
