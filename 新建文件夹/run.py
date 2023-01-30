import os
import time

import pandas as pd
from initialize_env import initialize_database
from process_csv import load_market_processed_pickle
from sqlite_core import SqliteCore

pd.options.display.max_columns = 1000


def market_data_entry_api(sql_core, market_data):
    # market_data分为股票数据和期权数据
    market_data_stock = market_data.pop('stock')
    market_data_option = market_data

    new_market_df = pd.read_sql('select * from market limit 0', sql_core.connection)
    new_instrument_df = pd.read_sql('select * from instrument limit 0', sql_core.connection)
    exist_instrument_df = pd.read_sql('select * from instrument', sql_core.connection)
    # market数据查重，之后会用到
    # exist_market_df = pd.read_sql('select * from market', sql_core.connection)

    query_instrument_df = exist_instrument_df[['instrument_id', 'instrument_name']]  # 是否需要新增instrument，相关查询的cache

    cur_market_id = sql_core.get_primary_idx('market')
    cur_instrument_id = sql_core.get_primary_idx('instrument')

    # 测试代码
    # print(market_data_stock.head(2))
    # print(market_data_stock.columns)
    # print(market_data_option['SPY'].head(2))
    # print(market_data_option['SPY'].columns)
    # return

    for idx, row in market_data_stock.iterrows():
        # 如果对应的instrument不存在，则需要添加instrument数据
        if row['symbol'] not in query_instrument_df['instrument_name'].values:
            new_instrument_df.loc[len(new_instrument_df)] = {
                'instrument_id': cur_instrument_id + 1,
                'instrument_name': row['symbol'],
                'description': row['description'],
                'instrument_type': row['assetType'],
                'underlying': None,
                'maturity': None,
                'strike': None,
                'option_type': None
            }
            cur_instrument_id += 1
            # 更新现存instrument暂存数据，类似cache，不用每次查找
            query_instrument_df = pd.concat(
                [exist_instrument_df[['instrument_id', 'instrument_name']],
                 new_instrument_df[['instrument_id', 'instrument_name']]], axis=0
            )

        new_market_df.loc[len(new_market_df)] = {
            'market_id': cur_market_id + 1,
            'timestamp': row['tradeTime'],
            'bid': row['bidPrice'],
            'ask': row['askPrice'],
            'mid': (row['bidPrice'] + row['askPrice']) / 2,
            'delta': None,
            'gamma': None,
            'thela': None,
            'vega': None,
            'rho': None,
            'volatility': None,
            'open_interest': None,
            'volume': row['totalVolume'],
            'last_price': row['lastPrice'],
            'instrument_id': int(
                query_instrument_df[query_instrument_df['instrument_name'] == row['symbol']]['instrument_id']
            ),
        }
        cur_market_id += 1

    for key, value in market_data_option.items():
        for idx, row in value.iterrows():
            # 如果对应的instrument不存在，则需要添加instrument数据
            if idx not in query_instrument_df['instrument_name'].values:
                new_instrument_df.loc[len(new_instrument_df)] = {
                    'instrument_id': cur_instrument_id + 1,
                    'instrument_name': idx,
                    'description': row['description'],
                    'instrument_type': 'option',
                    'underlying': key,
                    'maturity': row['T'],
                    'strike': row['K'],
                    'option_type': row['putCall']
                }
                cur_instrument_id += 1
                # 更新现存instrument暂存数据，类似cache，不用每次查找
                query_instrument_df = pd.concat(
                    [exist_instrument_df[['instrument_id', 'instrument_name']],
                     new_instrument_df[['instrument_id', 'instrument_name']]], axis=0
                )

            new_market_df.loc[len(new_market_df)] = {
                'market_id': cur_market_id + 1,
                'timestamp': row['tradeTime'],
                'bid': row['bid'],
                'ask': row['ask'],
                'mid': row['mark'],
                'delta': row['delta'],
                'gamma': row['gamma'],
                'thela': row['theta'],
                'vega': row['vega'],
                'rho': row['rho'],
                'volatility': row['volatility'],
                'open_interest': row['openInterest'],
                'volume': row['totalVolume'],
                'last_price': None,
                'instrument_id': int(
                    query_instrument_df[query_instrument_df['instrument_name'] == idx]['instrument_id']
                ),
            }
            cur_market_id += 1

    sql_core.add_data('instrument', new_instrument_df)
    sql_core.add_data('market', new_market_df)


if __name__ == '__main__':
    # 初始化数据库
    db_file_path = 'database_folder/test_0120.db'
    if os.path.exists(db_file_path):
        os.remove(db_file_path)
    sql_core = SqliteCore(db_file_path)
    initialize_database(sql_core)

    # 存market数据
    market_data = load_market_processed_pickle('raw_data_20230119140020.pickle')

    start_time = time.time()
    market_data_entry_api(sql_core, market_data)
    end_time = time.time()
    print('程序运行时间为: {}秒'.format(end_time - start_time))

    print(pd.read_sql('select * from market', sql_core.connection))
