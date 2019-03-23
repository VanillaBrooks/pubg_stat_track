# outside libraries
import discord
import requests
import seaborn as sns
import pandas as pd
import matplotlib.pyplot as plt

from pprint import pprint

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

stats_weights = {
    'kills': 1,
    'damageDealt': .3/100,
    'revives': .5
}

valid_fields = 'DBNOs assists boosts damageDealt headshotKills heals kills revives rideDistance timeSurvived weaponsAcquired winPlace'.split(' ')

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

class ReturnData():
    def __init__(self, user_list, data, fields):
        self.data= data
        self.users = user_list
        self.fields = fields

class MyClient(discord.Client):

    async def on_ready(self):
        print(f'ready {self.user}')



        # This block is for moving michael to his resting place if hes deaf
        MICHAELS_RESTING_PLACE_CHANNEL = discord.utils.get(
            client.get_all_channels(), server__name='Anger Central', name="Michael's Resting Place")

        while True:
            await asyncio.sleep(5)

            channels = client.get_all_channels()

            for channel in channels:
                for member in channel.voice_members:
                    print(str(member))
                    if str(member) == "LEGIQn#7532":
                        if member.voice.self_deaf:
                            try:
                                await client.move_member(member, MICHAELS_RESTING_PLACE_CHANNEL)
                            except Exception:
                                print('there was an error moving michael to a new channel')

    async def on_message(self, message):
        if str(message.author) == 'pubg_bot#0654':
            return None
        if '?pubg' in message.content:
            if "points" in message.content:
                print('in stats')
                result = await self.get_data(message)

                points = await calculate_points(result)
                await self.send_points(points, message.channel)
            elif 'stats' in message.content:
                result = await self.get_data(message)

                await self.send_stats(result, message.channel)

            elif 'fields' in message.content:
                str_to_fmt = '```Valid fields to query:\n'
                str_to_fmt += ''.join(i + ' ' for i in valid_fields)
                str_to_fmt += '\n```'
                await client.send_message(message.channel, str_to_fmt)

            elif "graph" in message.content:
                result = await self.get_data(message)
                # df = pd.DataFrame(result.data)
                
                df_dict = {}
                for field in stats_fields:
                    df_dict[field] = []
                    for user in result.users:

                        # this block calculates the cumulative sum of each element 
                        # based on the elements that have come before it 
                        data = result.data[user][field]
                        cumulative_sum = []
                        for i in range(len(data)):
                            dval = data[i]      # TODO: call the function to calculate points if `points` is mentioend as a field
                            if i !=0:
                                dval += cumulative_sum[i-1]
                            cumulative_sum.append(dval)

                        df = pd.DataFrame(cumulative_sum)
                        df.columns = [user]
                        df_dict[field].append(df)
                # for field in result.fields:
                await construct_graph(df_dict, 'damageDealt')
                await client.send_file(message.channel, "graph.png")
                os.remove("graph.png")
                
            else:
                help_str = "```USAGE: \n?pubg <stats> <hours>\n?pubg <graph> <hours> <space separated catagories> \
                    \nPossible catagories (case sensitive): kills, damageDealt, revives```"
                await client.send_message(message.channel, help_str)

    # find all users playing in a channel
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

        users.append('Captain_Crabby')
        print('users are: ', users)                                                                                     # manually adding stats herre

        return users
                
    # fetch data from the pubg api 
    async def get_data(self, message):
        hours = 10
        field_args = []
        capture_args = False
        for item in message.content.split(' '):
            if capture_args:     # capture all fields after the digit
                field_args.append(item)
            if item.isdigit():
                hours = int(item)
                capture_args = True

        current_time_utc = datetime.datetime.utcnow()
        query_time = current_time_utc - datetime.timedelta(hours=hours)

        print('field args before ', field_args)
        if len(field_args) == 0: # if no args were specified we use the default 3
            field_args = stats_fields
        print('field args are', field_args)

        pubg_user_list = await self.construct_user_list(message.author)

        rosters = await pubg_api.get_relevant_rosters(pubg_user_list, query_time)
        data = await pubg_api.parse_roster_stats(pubg_user_list, field_args, rosters)
        

        return ReturnData(pubg_user_list, data, field_args)

    # send out the stats to a discord channel
    async def send_points(self, points, channel):
        str_to_fmt = '```Points:\n'
        for key in points:
            point_val = points[key]
            str_to_fmt += f'{key}: {point_val} \n'
        str_to_fmt += '```'
        await client.send_message(channel, str_to_fmt)
    async def send_stats(self, result, channel):
        str_to_fmt = '```Stats: '
        for field in result.fields:
            str_to_fmt += field + ' '
        str_to_fmt += '\n'
        
        for user in result.users:
            str_to_fmt += user + ' '
            for field in result.fields:
                str_to_fmt += str(sum(result.data[user][field])) + ' '
            str_to_fmt+='\n'
        str_to_fmt += '```'
        print(str_to_fmt)
        await client.send_message(channel, str_to_fmt)

async def calculate_points(result):
    points = {user: 0 for user in result.users}
    
    for user_key in result.data:
        for field_key in result.data[user_key]:

            result.data[user_key][field_key] = sum(result.data[user_key][field_key])

            points[user_key] += result.data[user_key][field_key] * \
                stats_weights[field_key]

    print(' dictionary data: ')
    pprint(result.data)
    print(' points data:  ')
    pprint(points)

    return points


# construct line graph and send to discord chat
async def construct_graph(df_dict, key):
    # concatenate the list of dataframes together
    data = pd.concat(df_dict[key], axis=1)#.fillna(0)
    print(data)
    sns.set(style="darkgrid")
    sns_plot =sns.lineplot(data=data).set_title(key)

    fig = sns_plot.get_figure()
    fig.savefig("graph.png")


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
