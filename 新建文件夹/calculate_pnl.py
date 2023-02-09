import datetime

import pandas as pd

from sqlite_core import SqliteCore


# 计算pnl
# 我需要知道是股票还是期权，计算的方式不同？
# 输入为order_id和exit时间

def cal_pnl(sql_core, input_info_df):
    for idx, row in input_info_df.iterrows():
        # order_info为my_order表的查询结果
        order_info = sql_core.query_row_by_single_condition('my_order', 'order_id', row['order_id'])
        instrument_id = order_info['instrument_id'][0]
        order_price = order_info['order_price'][0]
        # instrument_info为instrument表的查询结果
        instrument_info = sql_core.query_row_by_single_condition('instrument', 'instrument_id', instrument_id)
        instrument_type = instrument_info['instrument_type'][0]
        # 如果是计算股票的PNL
        if instrument_type == 'EQUITY':
            # market_info为market表的查询结果
            market_info = sql_core.query_row_by_several_condition('market', {
                'instrument_id': instrument_id,
                'timestamp': row['exit_info'],
            })
            exit_price = market_info['mid'][0]
            print('股票的PNL为{}'.format(exit_price - order_price))
        # print(sql_core.query_row_by_single_condition('market', 'instrument_id', int(order_info['instrument_id'])))
        #
        # print(order_info)
        # print(instrument_info)
        # print(instrument_type)


if __name__ == '__main__':
    pd.options.display.max_columns = 1000
    my_sql_core = SqliteCore('database_folder/test_0120.db')
    cal_pnl(my_sql_core, pd.DataFrame({
        'order_id': 1,
        # 'exit_info': datetime.datetime(2022, 1, 22, 16, 0),
        'exit_info': '2023-01-19 13:45:20',
    }, index=[0]))
    # print(pd.read_sql('select * from market', my_sql_core.connection))
