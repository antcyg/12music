import datetime

import pandas as pd

from sqlite_core import SqliteCore


# 计算pnl
# 我需要知道是股票还是期权，计算的方式不同？
# 输入为order_id和exit时间

def cal_pnl(sql_core, input_info_df):
    for idx, row in input_info_df.iterrows():
        print(sql_core.query_row_by_single_condition('my_order', 'order_id', row['order_id']))


if __name__ == '__main__':
    my_sql_core = SqliteCore('database_folder/test_0120.db')
    cal_pnl(my_sql_core, pd.DataFrame({
        'order_id': 1,
        'exit_info': datetime.datetime(2022, 1, 22, 16, 0),
    }, index=[0]))
    # print(pd.read_sql('select * from my_order', my_sql_core.connection))
