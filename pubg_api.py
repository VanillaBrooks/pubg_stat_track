import pubg_python
from pprint import pprint
from api import pubg_secret
import datetime as dt

#delete later
import time

# parse the strings from the api to a datetime object 
# EXAMPLE STRING: '2019-03-16T22:49:19Z'
async def date_parse_from_string(input_string):
    time_obj = dt.datetime.strptime(input_string, '%Y-%m-%dT%H:%M:%SZ')
    # print(f'time object is {time_obj}')

    return time_obj

async def get_relevant_rosters(player_list, start_time):
    api = pubg_python.PUBG(pubg_secret, pubg_python.Shard.PC_NA)
    all_rosters = []
    analyzed_matches = []

    for current_player in player_list:              # todo: use player_list instead
        player = api.players().filter(player_names=[current_player])[0]  # player_list later
        
        for match_id in player.matches:

            if str(match_id) in analyzed_matches:
                continue # already parsed this match

            analyzed_matches.append(str(match_id))

            match_data = api.matches().get(match_id)
                
            if await date_parse_from_string(match_data.created_at) < start_time:
                break # no longer looking at matches from active session
            
            all_rosters += await find_all_rosters(match_data, player_list)

    return all_rosters

# start paring through the rosters
async def find_all_rosters(match_data, player_list):
    rosters_to_check = []

    for roster in match_data.rosters:

        for person in roster.participants:
            if person.name in player_list:
                rosters_to_check.append(roster)
                break

    return rosters_to_check

async def parse_roster_stats(player_list, fields, rosters):
    data = {player : {field: [] for field in fields} for player in player_list}

    for roster in rosters:
        for person in roster.participants:
            if person.name in player_list:
                # start parsing stats for that person
                stats = person.stats
                for field in fields:
                    data[person.name][field].append(stats[field])


    return data
