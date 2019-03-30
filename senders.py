import utils
import pandas as pd

async def send_stats(client, result, channel, logging):
    logging.info('converting dictionary to table')
    str_to_fmt = await utils.dict_to_table(result.stat_totals(), logging)
    logging.info('sending message')
    await client.send_message(channel, str_to_fmt)
    


async def send_combo(client, data_dict, channel, logging):
    logging.info('converting dictionary to table')
    str_to_fmt = await utils.dict_to_table(data_dict, logging)
    logging.info('sending message')
    await client.send_message(channel, str_to_fmt)


# send out the points to a discord channel
async def send_points(client, points, channel, logging):
    logging.info('converting dictionary to table')
    str_to_fmt = await utils.dict_to_table(points, logging)
    logging.info('sending message')

    await client.send_message(channel, str_to_fmt)

# TODO: this shit errors if there is no data for one of the users. 
async def graph(client, result, message, logging):
    logging.info(f'handling graphing')
    df_dict = {}
    for field in result.fields:
        df_dict[field] = []
        logging.debug(f"GRAPH: handling field {field}")
        for user in result.users:
            logging.debug(f"GRAPH: handling user {user}")
            # this block calculates the cumulative sum of each element
            # based on the elements that have come before it
            logging.debug(f'GRAPH: fetching data from result')
            data = result.data[user][field]

            cumulative_sum = []
            for i in range(len(data)):
                # TODO: call the function to calculate points if `points` is mentioend as a field
                dval = data[i]
                if i != 0:
                    dval += cumulative_sum[i-1]
                logging.debug(f"GRAPH: ITERATION {i} with current cumulative sum {dval} (data: {data[i]})")
                cumulative_sum.append(dval)
            if cumulative_sum == 0:
                logging.debug(f"GRAPH: cumulative sum for user {user} was zero we are not adding to df")
                continue
            logging.debug(f"GRAPH: finished cumulaitve sum: adding to dataframe")
            df = pd.DataFrame(cumulative_sum)
            logging.debug(f"GRAPH: dataframe done, adding columns")
            df.columns = [user]
            logging.debug(f'GRAPH: adding to list')
            df_dict[field].append(df)
    logging.info(f'sending dataframe data to grapher')
    for field in result.fields:
        logging.debug(f"sending {field} to graph")
        await utils.construct_graph(df_dict, field, logging)
        await client.send_file(message.channel, "graph.png")

    return df_dict


