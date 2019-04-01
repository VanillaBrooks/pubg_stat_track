import pubg_python
from pprint import pprint
from api import pubg_secret
import datetime as dt
import asyncio
#delete later
import time

# parse the strings from the api to a datetime object 
# EXAMPLE STRING: '2019-03-16T22:49:19Z'
async def date_parse_from_string(input_string):
    time_obj = dt.datetime.strptime(input_string, '%Y-%m-%dT%H:%M:%SZ')
    # print(f'time object is {time_obj}')
    return time_obj

async def get_relevant_rosters(player_list, start_time, logging, client, query_channel):
    api = pubg_python.PUBG(pubg_secret, pubg_python.Shard.PC_NA)
    all_rosters = []
    no_player_data = []
    analyzed_matches = []

    for current_player in player_list:              # todo: use player_list instead
        exception = True
        while exception:
            try:
                player = api.players().filter(player_names=[current_player])[0]  # player_list later
                exception = False
            except pubg_python.exceptions.RateLimitError:
                await client.send_message(query_channel, 'rate limited. continuing in 10 seconds')
                await asyncio.sleep(10)
        
        # player has no matches on the active patch. this prevents the query from crashing
        try:player_matches = player.matches
        except Exception: 
            logging.exception(f"player {current_player} has no matches in the current patch")
            # client.send_message(query_channel, f"player {current_player} has no matches in the current patch")
            no_player_data.append(current_player)
            continue
            
        for match_id in player.matches:
            logging.info(f"checking {match_id} from matches for {current_player}")

            if str(match_id) in analyzed_matches:
                logging.info(f"{match_id} has already been copied over")
                continue # already parsed this match

            analyzed_matches.append(str(match_id))

            exception = True
            while exception:
                try:
                    match_data = api.matches().get(match_id)
                    exception = False
                except pubg_python.exceptions.RateLimitError:
                    await client.send_message(query_channel, 'rate limited. continuing in 10 seconds')
                    await asyncio.sleep(10)

                    
            if await date_parse_from_string(match_data.created_at) < start_time:
                logging.info(f"match start time {start_time} is outside the time parameter; breaking")
                break # no longer looking at matches from active session
            
            all_rosters += await find_all_rosters(match_data, player_list, logging)
    
    ApiData = ApiResult(player_list, no_player_data, all_rosters)
    

    return ApiData

# start paring through the rosters
async def find_all_rosters(match_data, player_list, logging):
    rosters_to_check = []

    for roster in match_data.rosters:

        for person in roster.participants:
            if person.name in player_list:
                logging.info(
                    f"{person.name} is in the roster adding the roster to to checked later: {[person.name for person in roster.participants]}")
                rosters_to_check.append(roster)
                break

    return rosters_to_check

async def parse_roster_stats(player_list, fields, rosters, logging):
    data = {player : {field: [] for field in fields} for player in player_list}

    for roster in rosters:
        for person in roster.participants:
            if person.name in player_list:
                # start parsing stats for that person
                stats = person.stats
                for field in fields:
                    data[person.name][field].append(stats[field])

    return data

class ApiResult():
    def __init__(self, player_list, no_player_data, all_rosters):
        self.player_list = player_list
        self.bad_players = no_player_data
        self.roster_data = all_rosters
    def clean_player_list(self):
        for i in self.bad_players:
            self.player_list.remove(i)
        return self.player_list
