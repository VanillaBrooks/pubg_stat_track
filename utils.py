import pubg_api
import matplotlib.pyplot as plt
import logging
import datetime
import pandas as pd
import seaborn as sns
import os

from pprint import pprint

# construct line graph and send to discord chat
async def construct_graph(df_dict, key, logging):
    '''
    Args: 
        df_dict: <dict> of pandas dataframes. The keys are the categories queried and the values
            are <list>s  dataframes associated with that data
        key: <str> of the type of data we are constructing the graph for
    '''
    logging.debug("about to clear graph")
    plt.clf()
    # concatenate the list of dataframes together
    logging.debug("concat franes")
    data = pd.concat(df_dict[key], axis=1)#.fillna(0)
    logging.debug("set stype")
    sns.set(style="darkgrid")
    logging.debug("make grid")
    sns_plot =sns.lineplot(data=data).set_title(key)
    logging.debug("add labels")
    plt.xlabel("games played")
    plt.ylabel("total {}".format(key))

    logging.debug("get figure")
    fig = sns_plot.get_figure()
    logging.debug("save figure")
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
                        level=logging.DEBUG,
                        format='%(asctime)s.%(msecs)03d %(levelname)s %(module)s - %(funcName)s: %(message)s',
                        datefmt='%Y-%m-%d %H:%M:%S')

    return logging


async def calculate_points(stats_weights, result, logging, list_format=False):
    '''
    Args:
        stats_weights: <dict> of fields and their associated weight
        result: <class: ReturnData> of data fetched from utils.get_data
    returns:
        <dict> with (key: value) pair of (username: point total)
    '''
    if list_format:
        points = {user: {"points": []} for user in result.users}
    else:
        points = {user: {"points": 0.0} for user in result.users}
    logging.info(f"starting to calculate points with with list_format {list_format}")

    for user_key in result.data:
        for field_key in result.data[user_key]:
            if not (field_key in list(stats_weights.keys())):
                continue

            weight = stats_weights[field_key]
            if list_format:
                data = [weight * i for i in result.data[user_key][field_key]]
                points[user_key]['points'].append(data)
            else:
                total_sum = sum(result.data[user_key][field_key])
                points[user_key]['points'] += total_sum * weight


    if list_format:
        for user in points:
            deep = []
            for i in range(len(points[user]['points'][0])):
                count = 0
                for sublist in points[user]['points']:
                    count += sublist[i]
                deep.append(round(count, 2))
            points[user]['points'] = deep

    else:
        for user in points:
            points[user]['points'] = round(points[user]['points'] ,2)

    print("points are ")
    pprint(points)
    return points


# ??????????????????????????????????????????????????????????? FIX THIS FUNCTION W/ REGEX
# fetch data from the pubg api 
async def get_data(message, stats_weights, discord_to_pubg, client, logging):
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

    if "extended" in field_args:
        field_args = "kills DBNOs damageDealt assists headshotKills heals boosts revives timeSurvived rideDistance weaponsAcquired points".split(' ')
    elif 'combo' in field_args:
        field_args = "kills damageDealt revives points".split(' ')

    current_time_utc = datetime.datetime.utcnow()
    query_time = current_time_utc - datetime.timedelta(hours=hours)
    logging.info(f"hours are parsed to be {hours}")
    logging.info(f"query start time UTC is {query_time}")

    if len(field_args) == 0: # if no args were specified we use the default 3
        field_args = list(stats_weights.keys())
    
    remove_later = []
    points_flag = False
    if "points" in field_args:
        points_flag = True
        field_args.remove("points")
        
        for i in list(stats_weights):
            if i not in field_args:
                remove_later.append(i)
                field_args.append(i)


    logging.info(f"arguments for fields to query are {field_args}")
        
    pubg_user_list = await construct_user_list(discord_to_pubg, message.author, client, logging)

    ApiResult = await pubg_api.get_relevant_rosters(pubg_user_list, query_time, logging, client, message.channel)
    pubg_user_list = ApiResult.clean_player_list() # remove data for users that dont have any api data
    data = await pubg_api.parse_roster_stats(pubg_user_list, field_args, ApiResult.roster_data, logging)
    

    # calculate the minimun number of games someone in the party has
    min_len = 0
    data_copy = dict(data)
    for user in data:
        for field in data[user]:
            L = len(data[user][field])
            if L == 0:
                logging.info(f"{user} is being removed from the query because they have no data")
                del data_copy[user]
                pubg_user_list.remove(user)
            elif min_len ==0:
                min_len = L
            elif L < min_len:
                min_len = L
            break
    
    # pop out data that is not congruent for everyone 
    for user in data:
        for field in data[user]:
            try: data_copy[user][field].reverse()
            except Exception: pass
            for _ in range(len(data[user][field])-min_len):
                data_copy[user][field].pop(0)
    
    return ReturnData(pubg_user_list, data_copy, field_args, points_flag, remove_later)


# find all users playing in a channel
async def construct_user_list(discord_to_pubg, author, client, logging):
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
    # users.append('Loko_Soko')
    # users += "TheGigoloJoe Poc_Poc Captain_Crabby Loko_Soko".split()

    # print('users are: ', users)                                                                                     # manually adding stats herre

    return users

# combine two dictionaries with the same keys
async def merge_dicts(*args):
    total = args[0]

    for i_ in args[1:]:
        for user in i_:
            for field in i_[user]:
                total[user][field] = i_[user][field]

    return total

class ReturnData():
    def __init__(self, user_list, data, fields, points_flag, to_be_removed):
        self.data = data
        self.users = user_list
        self.fields = fields
        self.points = points_flag
        self.remove_args = to_be_removed

    # return a copy of the dictionary with summed and rounded values
    def stat_totals(self):
        copy = dict(self.data)
        for user_key in copy:
            for field_key in copy[user_key]:
                copy[user_key][field_key] = round(sum(copy[user_key][field_key]), 1)
        return copy

    def data_copy(self):
        return dict(self.data)

    def clean_data(self):
        cpy = dict(self.data)
        print(f"\n\n fields are {self.fields} to be removed are {self.remove_args} ")
        for user in self.data:
            for arg in self.remove_args:
                del cpy[user][arg]
        for arg in self.remove_args:
            self.fields.remove(arg)
        self.data = cpy
        
        if self.points:
            self.fields += ['points']

    def __len__(self):
        return len(self.users)

# get the maximum lenth of all the data in a dictionary
# TODO: Return a dictionary with the length associated with each column instead
#       as currenly there is wasted space
async def find_max_length(input_dict, logging):
    max_len = 0
    sample_user = list(input_dict.keys())[0]
    len_dict = {field: 0 for field in input_dict[sample_user]}
    len_dict["username"] = 0


    def change_len(x, len_dict, field, raw = False):
        if field == "username":
            data = x
        elif raw == True:
            data = field
        else:
            data = str(input_dict[x][field])
        length = len(data)
            
        if length > len_dict[field]:
            len_dict[field] = length

        return len_dict

    for username in input_dict:
        len_dict = change_len(username, len_dict, "username")
        
        for field in input_dict[username]:
            len_dict = change_len(username, len_dict, field, raw=True)

            str_data = str(input_dict[username][field])
            len_dict = change_len(username, len_dict, field)
 
    return len_dict

# format a dictionary as a string to be sent off
async def dict_to_table(dict_to_fmt, logging):
    len_dict = await find_max_length(dict_to_fmt, logging)

    # right justifies a string with spaces
    # https://docs.python.org/3/library/stdtypes.html#str.format
    def add_str(x, s, field):
        new = "{: >{width}}".format(x, width = len_dict[field]+1)
        return s + new

    str_to_fmt = "```"
    str_to_fmt = add_str("username", str_to_fmt, "username")

    # add fields / column titles


    for field in dict_to_fmt[list(dict_to_fmt.keys())[0]]:
        str_to_fmt = add_str(field, str_to_fmt, field)

    str_to_fmt += "\n"

    # add data and usernames to the rows
    for user in dict_to_fmt:
        str_to_fmt = add_str(user, str_to_fmt, "username")
        for field in dict_to_fmt[user]:
            str_to_fmt = add_str(str(dict_to_fmt[user][field]), str_to_fmt, field)
        str_to_fmt += "\n"
    
    str_to_fmt += '```'
    # return the formatted table
    return str_to_fmt
