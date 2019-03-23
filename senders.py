from utils import construct_graph
import pandas as pd

async def send_stats(client, result, channel):
    str_to_fmt = '```Stats: '
    for field in result.fields:
        str_to_fmt += field + ' '
    str_to_fmt += '\n'
    
    for user in result.users:
        str_to_fmt += user + ' '
        for field in result.fields:
            user_stat_sum = sum(result.data[user][field])
            str_to_fmt += str(round(user_stat_sum, 0)) + ' '
        str_to_fmt+='\n'
    str_to_fmt += '```'
    
    print(str_to_fmt)

    await client.send_message(channel, str_to_fmt)


async def send_combo(client, result, points,  channel):
    str_to_fmt = '```Stats: '
    for field in result.fields:
        str_to_fmt += field + ' '
    str_to_fmt += str('points')
    str_to_fmt += '\n'

    for user in result.users:
        str_to_fmt += user + ' '
        for field in result.fields:
            str_to_fmt += str(round(result.data[user][field], 0)) + ' '
        str_to_fmt += str(points[user])
        str_to_fmt += '\n'
    str_to_fmt += '```'
    
    await client.send_message(channel, str_to_fmt)


# send out the points to a discord channel
async def send_points(client, points, channel):
    str_to_fmt = '```Points:\n'
    for key in points:
        point_val = points[key]
        str_to_fmt += f'{key}: {point_val} \n'
    str_to_fmt += '```'

    await client.send_message(channel, str_to_fmt)


async def graph(client, result, message):
    df_dict = {}

    for field in result.fields:
        df_dict[field] = []
        for user in result.users:

            # this block calculates the cumulative sum of each element
            # based on the elements that have come before it
            data = result.data[user][field]
            cumulative_sum = []
            for i in range(len(data)):
                # TODO: call the function to calculate points if `points` is mentioend as a field
                dval = data[i]
                if i != 0:
                    dval += cumulative_sum[i-1]
                cumulative_sum.append(dval)

            df = pd.DataFrame(cumulative_sum)
            df.columns = [user]
            df_dict[field].append(df)

    for field in result.fields:
        await construct_graph(df_dict, field)
        await client.send_file(message.channel, "graph.png")

    return df_dict


