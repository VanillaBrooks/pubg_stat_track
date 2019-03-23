import utils
import pandas as pd

async def send_stats(client, result, channel):
    str_to_fmt = await utils.dict_to_table(result.stat_totals())

    await client.send_message(channel, str_to_fmt)


async def send_combo(client, data_dict,  channel):

    str_to_fmt = await utils.dict_to_table(data_dict)
    
    await client.send_message(channel, str_to_fmt)


# send out the points to a discord channel
async def send_points(client, points, channel):

    str_to_fmt = await utils.dict_to_table(points)

    await client.send_message(channel, str_to_fmt)

# TODO: this shit errors if there is no data for one of the users. 
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
        await utils.construct_graph(df_dict, field)
        await client.send_file(message.channel, "graph.png")

    return df_dict


