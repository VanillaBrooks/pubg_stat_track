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
    'happypenguin#9475': 'Happy--Penguin',
    'Torrannosaurusrex#1167': 'Prowler337'
}


class MyClient(discord.Client):

    async def on_ready(self):
        print(f'ready {self.user}')

    async def on_message(self, message):
        if str(message.author) == 'StoryTeller#2596':
            return None
        if '?pubg' in message.content:

            if "points" in message.content:
                result = await utils.get_data(message, stats_weights, discord_to_pubg, client)
                print("users from result, ", result.users)
                points = await utils.calculate_points(stats_weights, result)
                await senders.send_points(client, points, message.channel)

            elif 'stats' in message.content:
                result = await utils.get_data(message, stats_weights, discord_to_pubg, client)
                await senders.send_stats(client, result, message.channel)

            elif 'fields' in message.content:
                str_to_fmt = '```Valid fields to query:\n'
                str_to_fmt += ''.join(i + ' ' for i in valid_fields)
                str_to_fmt += '\n```'
                await client.send_message(message.channel, str_to_fmt)

            elif "graph" in message.content:
                result = await utils.get_data(message, stats_weights, discord_to_pubg, client)
                await senders.graph(client, result, message)

                os.remove("graph.png")

            elif 'combo' in message.content:
                result = await utils.get_data(message, stats_weights, discord_to_pubg, client)
                points = await utils.calculate_points(stats_weights, result)
                combined = await utils.merge_dicts(result.stat_totals(), points)
                
                await senders.send_combo(client, combined, message.channel)

            else:
                help_str = "```USAGE: \n?pubg <stats> <hours>\n?pubg <graph> <hours> <space separated catagories> \
                    \nPossible catagories (case sensitive): kills, damageDealt, revives```"
                await client.send_message(message.channel, help_str)


if __name__ == '__main__':
    logging = utils.logger_config()
    client = MyClient()
    client.run(discord_token)
