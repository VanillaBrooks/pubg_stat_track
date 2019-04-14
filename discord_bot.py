# outside libraries
import discord
import requests
import seaborn as sns
import pandas as pd

from pprint import pprint

# std lib
import os
import time
import asyncio

# local files
from api import discord_token
import senders
import utils

# fields of the stats that we care about
stats_weights = {
    'kills': .7,
    'damageDealt': .3/100,
    'revives': .5
}

valid_fields = 'DBNOs assists boosts damageDealt headshotKills heals kills revives rideDistance timeSurvived weaponsAcquired winPlace'.split(' ')

# conversion from discord name to pubg username
discord_to_pubg = {
    'Big Dick Bandit#8045': 'Loko_Soko',
    'Gigolojoe#7817': 'TheGigoloJoe',
    'PocPoc#7403': 'Poc_Poc',
    'Croutons#7324': 'SandyBrooks',
    'colbykarlik#0348':'Captain_Crabby',
    'LEGIQn#7532':'LEGIQn_',
    'Joeyeyey#8697' : 'Joeyeyey',
    'happypenguin#9475': 'Happy--Penguin',
    'Torrannosaurusrex#1167': 'Prowler337'
}


class MyClient(discord.Client):

    async def on_ready(self):
        print(f'ready {self.user}')

        resting_place = channel = discord.utils.get(
            client.get_all_channels(), server__name='Anger Central', name="Michael's Resting Place")
        main_channel = channel = discord.utils.get(
            client.get_all_channels(), server__name='Anger Central', name="main")

        while True:
            all_channels = client.get_all_channels()
            for channel in all_channels:
                for member in channel.voice_members:
                    # print(f'{member.id}, {member.name}')
                    # brooks: 83987573919191040
                    if int(member.id) in [119628439610195970]:

                        logging.info(f"michael is in channel {channel.name} WITH ID: {channel.id}")

                        # if micahel is deaf and he is not already in his resting place
                        if member.self_deaf and  int(channel.id) != 558874519629070346:
                            logging.info("michael is deaf, moving to new channel")
                            try:
                                await client.move_member(member, resting_place)
                                await client.send_message(main_channel, 'Michael will now rest')
                            except Exception:
                                logging.exception(f"Michael was not able to be moved from {channel.name}")
            await asyncio.sleep(5)

    async def on_message(self, message):
        if str(message.author) == 'StoryTeller#2596':
            return None
        logging.info(f"new query ({message.id}) recieved from {message.author}: {message.content}")
        print(f"new query ({message.id}) recieved from {message.author}: {message.content}")
        if '?pubg' in message.content:

            if 'stats' in message.content:
                logging.info(f"handling {message.id} for stats")
                result = await utils.get_data(message, stats_weights, discord_to_pubg, client, logging)

                if result.points:
                    points = await utils.calculate_points(stats_weights, result, logging, True)
                    result.data = await utils.merge_dicts(result.data_copy(), points)
                    result.clean_data()

                if not len(result): return False

                await senders.send_stats(client, result, message.channel, logging)

            elif 'fields' in message.content:
                logging.info(f"handling {message.id} for fields")

                str_to_fmt = '```Valid fields to query:\n'
                str_to_fmt += ''.join(i + ' ' for i in valid_fields) + '\n```'

                await client.send_message(message.channel, str_to_fmt)

            elif "graph" in message.content:
                logging.info(f"handling {message.id} for graph")
                result = await utils.get_data(message, stats_weights, discord_to_pubg, client, logging)

                if not len(result): return False

                if result.points:
                    points = await utils.calculate_points(stats_weights, result, logging, True)
                    result.data = await utils.merge_dicts(result.data_copy(), points)
                    result.clean_data()

                await senders.graph(client, result, message, logging)

                os.remove("graph.png")

            else:
                help_str = "```USAGE: \n?pubg <stats> <hours> <space separated categories>\
                    \n?pubg <graph> <hours> <space separated catagories> \
                    \nPossible catagories are:\
                    \n{cats}\
                    \nadditional keywords for multiple categories:\
                    \ncombo: kills damageDealt revives points\
                    \nextended: kills DBNOs damageDealt assists headshotKills hea ls boosts revives timeSurvived rideDistance weaponsAcquired points\
                    \n\nExamples:\
                    \n?pubg stats 3 combo\
                    \n?pubg stats 2 extended\
                    \n?pubg graph 6 damageDealt heals revives\
                    \n?pubg graph 3 combo\
                    ```".format(cats=''.join(i + " " for i in valid_fields))
                await client.send_message(message.channel, help_str)

logging = utils.logger_config()
if __name__ == '__main__':
    # from api_brooksie import discord_token
    logging = utils.logger_config()
    client = MyClient()
    client.run(discord_token)
