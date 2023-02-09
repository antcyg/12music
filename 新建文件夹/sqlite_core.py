import sqlite3
import pandas as pd


class SqliteCore(object):
    def __init__(self, db_path):
        self.connection = sqlite3.connect(db_path)
        self.primary_idx_dict = {}

    def creat_table(self, table_name, para_list):
        sql_cmd = 'CREATE TABLE IF NOT EXISTS {}('.format(table_name)
        for idx in range(len(para_list) - 1):
            para_list[idx] += ','
        for para in para_list:
            sql_cmd += para
        sql_cmd += ')'
        self.connection.execute(sql_cmd)

    def add_data(self, table_name, data_df, exists_type='append'):
        data_df.to_sql(table_name, con=self.connection, if_exists=exists_type, index=False)

    def get_primary_idx(self, table_name, primary_key=None):
        if primary_key is None:
            primary_key = table_name + '_id'
        res = pd.read_sql('select * from {} order by {} desc'.format(table_name, primary_key), self.connection)
        cur_primary_id = 0 if res.empty else res.loc[0][primary_key]
        self.primary_idx_dict[table_name] = cur_primary_id
        return cur_primary_id

    # 适用于input_col是唯一的 scan
    # like abcxxxx比xxxxabc快
    # perfer inner join
    # where avoid function
    def query_0(self, table_name, input_col, input_value, target_col):
        res = pd.read_sql('select {} from {} where {}={}'.format(target_col, table_name, input_col, input_value),
                          self.connection)
        return res[target_col]

    def query_current_position_by_instrument_id(self, instrument_id):
        res = pd.read_sql(
            'select position_id from position where instrument_id={} and enddate is null'.format(instrument_id),
            self.connection)
        return res

    def update(self, table_name, set_value_dict, condition_str):
        command = 'UPDATE {} SET'.format(table_name)
        for key, value in set_value_dict.items():
            value = "'{}'".format(value) if not isinstance(value, int) else value
            command += ' {}={},'.format(key, value)
        command = command.rstrip(',')
        command += ' WHERE {}'.format(condition_str)
        self.connection.execute(command)

    def query_col_to_list(self, table_name, target_col):
        """
        用来查询某张表的某一列，转换成列表并输出
        param:
            table_name: 表名
            target_col: 要查询的列名
        """
        return pd.read_sql('select {0} from {1}'.format(target_col, table_name), self.connection)[target_col].to_list()

    def query_row_by_single_condition(self, table_name, condition_col, condition_value):
        res = pd.read_sql('select * from {} where {}={}'.format(table_name, condition_col, condition_value),
                          self.connection)
        return res

    def query_row_by_several_condition(self, table_name, condition_dict):
        cmd = 'select * from {} where'.format(table_name)
        for condition_col, condition_value in condition_dict.items():
            condition_value = "'{}'".format(condition_value) if isinstance(condition_value, str) \
                else condition_value
            cmd += ' {} = {} and'.format(condition_col, condition_value)
        cmd = cmd.rstrip(' and')
        res = pd.read_sql(cmd, self.connection)
        return res

    def get_foreign_key(self, input_value, foreign_key_table=None, input_col=None, foreign_key_col=None, cache=None):
        if cache is not None:
            return int(cache[cache[input_col] == input_value][foreign_key_col])
        else:
            # todo:没有cache的情况
            pass
