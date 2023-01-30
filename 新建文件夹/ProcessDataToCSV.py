import pandas as pd
from datetime import datetime as dt
import pytz
import json
import pickle

EST = pytz.timezone('US/Eastern')
DT_FORMAT = '%Y-%m-%d %H:%M:%S'

def convert_epoch_time_in_milliseconds_into_datetime_est(epoch_time: int):
    dt_result = dt.utcfromtimestamp(epoch_time / 1000)  # epoch -> utc
    dt_result = dt_result.replace(tzinfo=pytz.UTC)  # make aware of timezone UTC
    dt_result = dt_result.astimezone(EST).strftime(DT_FORMAT)  # utc -> est
    return dt_result


def preprocess_stock_quotes(json_data):
    # convert json_data into pandas dataframe
    df = pd.DataFrame(json_data).T
    df.index.name = 'ticker'

    # convert time columns into %Y-%m-%d %H:%M:%S EST
    time_cols = ['quoteTimeInLong', 'tradeTimeInLong', 'regularMarketTradeTimeInLong']
    time_cols_new = ['quoteTime', 'tradeTime', 'timestamp']
    replace_dict = dict(zip(time_cols, time_cols_new))
    df.loc[:, time_cols] = df[time_cols].applymap(convert_epoch_time_in_milliseconds_into_datetime_est)
    df.rename(columns=replace_dict, inplace=True)

    # set timestamp as index
    df = df.reset_index().set_index('timestamp')

    return df


def json_normalize_option_chain(option_chain):
    df = pd.DataFrame(option_chain).T  # each row is a maturity, each column is a strike
    df.reset_index(inplace=True)
    df = df.melt(id_vars=[
        'index'])  # each row is a combo of maturity and strike, its value is a list of size 1, the element is a dictionary
    df.dropna(inplace=True)

    df_sub = df['index'].str.split(':', expand=True)  # index columns is e.g. 2022-12-31:10 (ExpiryDate:DaysToExpiry)
    df_sub.columns = ['T', 'daysToExpiry']

    res = df.value.apply(lambda elem: pd.Series(elem[0]))  # convert each cell into a pandas series
    cols = res.columns

    res['T'] = df_sub['T']
    res['daysToExpiry'] = df_sub['daysToExpiry']
    res['K'] = df['variable']
    res = res[['T', 'K'] + list(cols) + ['daysToExpiry']]  # make T, K the first two columns

    res.reset_index(drop=True, inplace=True)
    res.set_index('symbol', inplace=True)
    return res


def preprocess_option_chains(json_data):
    volatility, num_contracts = json_data['volatility'], json_data['numberOfContracts']
    call_option_chain = json_normalize_option_chain(json_data['callExpDateMap'])
    put_option_chain = json_normalize_option_chain(json_data['putExpDateMap'])
    all_option_chain = pd.concat([call_option_chain, put_option_chain])

    # convert time columns into %Y-%m-%d %H:%M:%S EST
    time_cols = ['quoteTimeInLong', 'tradeTimeInLong', 'lastTradingDay']
    time_cols_new = ['quoteTime', 'tradeTime', 'lastTradingDay']
    replace_dict = dict(zip(time_cols, time_cols_new))
    all_option_chain.loc[:, time_cols] = all_option_chain[time_cols].applymap(
        convert_epoch_time_in_milliseconds_into_datetime_est)
    all_option_chain.rename(columns=replace_dict, inplace=True)
    return volatility, num_contracts, all_option_chain

file_name = "raw_data_20230119210020.json"
data = json.load(open(file_name))
stock_data = data['stock']
df_stock_data = preprocess_stock_quotes(stock_data)
option_ticker_list = ((key, key.split('_')[1]) for key in data.keys() if key != 'stock')
result = {}
result['stock'] = df_stock_data
for k, v in option_ticker_list:
    df_sub = preprocess_option_chains(data[k])
    result[v] = df_sub
file_name_pickle = file_name.replace(".json", ".pickle")

with open(file_name_pickle, 'wb') as handle:
    pickle.dump(result, handle, protocol=pickle.HIGHEST_PROTOCOL)

'''
import pickle

file_name_pickle = 'raw_data_20221209213020.pickle'
# open a file, where you stored the pickled data
with open(file_name_pickle, 'rb') as file:
    data = pickle.load(file)

ticker_list = [k for k in data.keys() if k != 'stock']
stock_quotes = data['stock']
volatility, num_contracts, option_chain = data['SPY']
'''