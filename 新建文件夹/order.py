import datetime

import pandas as pd

from sqlite_core import SqliteCore


def place_order_api(sql_core, order_info_df):
    new_order_df = pd.read_sql('select * from my_order limit 0', sql_core.connection)
    cur_order_id = sql_core.get_primary_idx('my_order', primary_key='order_id')  # order表主键
    query_instrument_df = pd.read_sql('select * from instrument', sql_core.connection)

    for idx, row in order_info_df.iterrows():
        instrument_id = sql_core.get_foreign_key(
            row['description'], cache=query_instrument_df, input_col='instrument_name', foreign_key_col='instrument_id'
        )
        new_order_df.loc[len(new_order_df)] = {
            'order_id': cur_order_id + 1,
            'instrument_id': instrument_id,
            'timestamp': row['timestamp'],
            'qty': row['qty'],
            'order_type': row['order_type'],
            'order_price': row['order_price'],
        }
        cur_order_id += 1
        sql_core.add_data('my_order', new_order_df)


# order_fill的情况
def complete_order_api(sql_core, complete_order_info_df):
    new_trade_df = pd.read_sql('select * from trade limit 0', sql_core.connection)
    cur_trade_id = sql_core.get_primary_idx('trade')  # trade表主键

    for idx, row in complete_order_info_df.iterrows():

        # 检查order是否已经被处理过了
        # str(row['order_id'])是因为外键读出来似乎是object
        if str(row['order_id']) in sql_core.query_col_to_list('trade', 'order_id'):
            print('order_id:{}添加失败，对应的order已完成'.format(row['order_id']))
            continue

        new_trade_df.loc[len(new_trade_df)] = {
            'trade_id': cur_trade_id + 1,
            'order_id': row['order_id'],
            'timestamp': row['timestamp'],
            'qty': row['qty'],
            'price': row['price'],
            'reason': row['reason'],
        }
        sql_core.add_data('trade', new_trade_df)
        cur_trade_id += 1

        instrument_id = int(sql_core.query_0(table_name='my_order', input_col='order_id', input_value=row['order_id'],
                                             target_col='instrument_id'))
        position_query_res = sql_core.query_current_position_by_instrument_id(instrument_id)
        position_id = None if position_query_res.empty else int(position_query_res['position_id'])

        new_position_df = pd.read_sql('select * from position limit 0', sql_core.connection)
        cur_position_id = sql_core.get_primary_idx('position')  # position表主键

        if position_id is None:
            # 对应的instrument在position中不存在的情况
            new_position_df.loc[len(new_position_df)] = {
                'position_id': cur_position_id + 1,
                # 'order_id': row['order_id'],
                'startdate': row['timestamp'],
                'qty': row['qty'],
                'instrument_id': instrument_id,
            }
            sql_core.add_data('position', new_position_df)
        else:
            sql_core.update('position', {'enddate': row['timestamp']}, 'position_id={}'.format(position_id))
            new_position_df.loc[len(new_position_df)] = {
                'position_id': cur_position_id + 1,
                'startdate': row['timestamp'],
                'qty': float(sql_core.query_0('position', 'position_id', position_id, 'qty')) + row['qty'],
                'instrument_id': instrument_id,
                'replace_position_id': position_id,
            }
            sql_core.add_data('position', new_position_df)


if __name__ == '__main__':
    pd.options.display.max_columns = 1000

    my_sql_core = SqliteCore('database_folder/test_0120.db')
    place_order_api(my_sql_core, pd.DataFrame({
        'description': 'AAPL',
        'timestamp': datetime.datetime(2022, 1, 22, 16, 0),
        'qty': 100,
        'order_type': 'limit',
        'order_price': 10.54,
    }, index=[0]))
    # print(pd.read_sql('select * from my_order', my_sql_core.connection))

    cur_order_id = my_sql_core.get_primary_idx('my_order', primary_key='order_id')  # order表主键
    complete_order_api(my_sql_core, pd.DataFrame({
        'order_id': cur_order_id,
        'timestamp': datetime.datetime(2022, 1, 22, 16, 0),
        'qty': 100,
        'price': 18.98,
        'reason': 'order fill',
    }, index=[0]))
    print(pd.read_sql('select * from position', my_sql_core.connection))
