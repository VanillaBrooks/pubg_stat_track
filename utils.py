import pubg_api
import matplotlib.pyplot as plt
import logging
import datetime
import pandas as pd
import seaborn as sns
import os

# construct line graph and send to discord chat
async def construct_graph(df_dict, key):
    '''
    Args: 
        df_dict: <dict> of pandas dataframes. The keys are the categories queried and the values
            are <list>s  dataframes associated with that data
        key: <str> of the type of data we are constructing the graph for
    '''
    plt.clf()
    # concatenate the list of dataframes together
    data = pd.concat(df_dict[key], axis=1)#.fillna(0)
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

    return logging


async def calculate_points(stats_weights, result):
    '''
    Args:
        stats_weights: <dict> of fields and their associated weight
        result: <class: ReturnData> of data fetched from utils.get_data
    returns:
        <dict> with (key: value) pair of (username: point total)
    '''
    points = {user: 0 for user in result.users}
    
    for user_key in result.data:
        for field_key in result.data[user_key]:

            result.data[user_key][field_key] = sum(result.data[user_key][field_key])

            points[user_key] += round(result.data[user_key][field_key] * \
                stats_weights[field_key], 2)

    return points


# fetch data from the pubg api 
async def get_data(message, stats_weights, discord_to_pubg, client):
    '''
    Args:
        message: <class: Discord.Message> the recieved message from discord
        stats_weights: <dict> of fields and their associated weight
        discord_to_pubg: <dict> of conversions between discord usernames and pubg usernames
    returns:
        <class: ReturnData> of the data fetched from the API
    '''

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
        field_args = list(stats_weights.keys())
    print('field args are', field_args)

    pubg_user_list = await construct_user_list(discord_to_pubg, message.author, client)

    rosters = await pubg_api.get_relevant_rosters(pubg_user_list, query_time)
    data = await pubg_api.parse_roster_stats(pubg_user_list, field_args, rosters)
    

    return ReturnData(pubg_user_list, data, field_args)


# find all users playing in a channel
async def construct_user_list(discord_to_pubg, author, client):
    '''
    Args:
        discord_to_pubg: <dict> of conversions between discord usernames and pubg usernames
        author: <class: Discord.user> of the person querying the bot
    Returns:
        <list> of users who are in the same channel as the `author` and are in `discord_to_pubg`
    '''
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

    # users.append('Captain_Crabby')
    # print('users are: ', users)                                                                                     # manually adding stats herre

    return users


class ReturnData():
    def __init__(self, user_list, data, fields):
        self.data = data
        self.users = user_list
        self.fields = fields
