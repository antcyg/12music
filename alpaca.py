import tushare as ts
import pandas as pd
import numpy as np

START_DATE = '20160101'  # 开始日期
ADJ = 'qfq'  # TODO:前复权，不知道啥意思

pro = ts.pro_api()
# 名称、code等数据
stock_basic = pro.stock_basic(exchange='', list_status='L', fields='ts_code,symbol,name,area,industry,list_date')
# 手动选择10个股票
code_list = ['600096', '600328', '000852', '601118', '603019', '600792', '300369', '300188', '600536', '000878',
             '600456', '600683']
StockList_basic = stock_basic[stock_basic['symbol'].apply(lambda s: s in code_list)].reset_index(drop=True)
TS_CODE_POOL = list(StockList_basic.ts_code)

INIT_AMOUNT = 5
INIT_CASH = 200000 / INIT_AMOUNT


# 根据code返回股票的df
def get_dataframe_from_code(code):
    """
    根据股票的code，生成包含所需信息的dataframe
    :param code: str，股票代码，e.g. '600536.SH'
    :return: 包含股票信息的dataframe
    """
    # 获取原始的股票信息dataframe
    info_df = ts.pro_bar(ts_code=code, adj=ADJ, start_date=START_DATE)
    info_df.index = pd.to_datetime(info_df['trade_date'])
    info_df = info_df.sort_index(ascending=True)

    return info_df


def random_select_from_ts_code_pool(amount=2):
    """
    从备选股池中随机选择若干支股票
    :param amount: 随机选择的个数
    :return: list，包含选择出的股票的code，选择失败则返回None
    """
    if len(TS_CODE_POOL) < amount:
        return None

    result = []
    for i in range(amount):
        length = len(TS_CODE_POOL)
        random_idx = np.random.randint(0, length)
        result.append(TS_CODE_POOL[random_idx])
        TS_CODE_POOL.pop(random_idx)

    return result


def judge_trade_day(date_str, code_df_dict):
    """
    判断某日是否为交易日
    :param date_str:
    :param code_df_dict:
    :return:
    """
    for code_df in code_df_dict.values():
        if date_str in code_df.index:
            return True
        else:
            return False


def back_test():
    # # cash、buy_price、position
    # info = np.array([[INIT_CASH for i in range(INIT_AMOUNT)], np.zeros(INIT_AMOUNT), np.zeros(INIT_AMOUNT)])
    # # info = np.ndarray([[INIT_CASH for i in range(INIT_AMOUNT)]])
    #
    # init_code_list = random_select_from_ts_code_pool(5)
    # code_info_dict = {}
    # for code in init_code_list:
    #     df = get_dataframe_from_code(code)
    #     code_info_dict[code] = df
    #
    # cur_date = pd.to_datetime(START_DATE)
    # print(cur_date)
    # cur_date += pd.offsets.BMonthBegin()
    # print(cur_date)
    # cur_date += pd.offsets.BMonthBegin()
    # print(cur_date)
    # cur_date += pd.offsets.BMonthBegin()
    # print(cur_date)
    # cur_date += pd.offsets.BMonthBegin()
    # print(cur_date)

    col_list = []
    for i in range(INIT_AMOUNT):
        col_list.extend(['code_{}'.format(i), 'cash_{}'.format(i), 'buy_price_{}'.format(i), 'position_{}'.format(i)])
    funds_df = pd.DataFrame(columns=col_list)

    init_code_list = random_select_from_ts_code_pool(5)
    code_df_dict = {code: get_dataframe_from_code(code) for code in init_code_list}

    # 从start_date开始寻找第一个交易日
    cur_date = pd.to_datetime(START_DATE)
    cur_date_str = cur_date.strftime('%Y-%m-%d')
    while not judge_trade_day(cur_date_str, code_df_dict):
        cur_date += pd.offsets.BDay(1)
        cur_date_str = cur_date.strftime('%Y-%m-%d')
    first_trade_date = cur_date
    first_trade_date_str = cur_date_str
    next_adjust_date = first_trade_date + pd.offsets.BMonthBegin(2)

    funds_df.loc[first_trade_date_str] = [np.nan, INIT_CASH, np.nan, 0] * INIT_AMOUNT
    for idx, code in enumerate(init_code_list):
        funds_df.loc[first_trade_date_str, 'code_{}'.format(idx)] = code

    count = 0
    while count < 5 and cur_date < next_adjust_date:
        for idx, code in enumerate(init_code_list):
            code_df = code_df_dict[code]
            if funds_df.loc[first_trade_date_str, 'buy_price_{}'.format(idx)] != np.nan and cur_date_str in code_df.index:
                buy_price = code_df.loc[cur_date_str, 'open']
                position = INIT_CASH / buy_price // 100 * 100
                cash = INIT_CASH - buy_price * position
                funds_df.loc[first_trade_date_str, 'buy_price_{}'.format(idx)] = buy_price
                funds_df.loc[first_trade_date_str, 'position_{}'.format(idx)] = position
                funds_df.loc[first_trade_date_str, 'cash_{}'.format(idx)] = cash
                count += 1
        cur_date += pd.offsets.BDay(1)
        cur_date_str = cur_date.strftime('%Y-%m-%d')
    print(funds_df)


if __name__ == '__main__':
    # code_list = random_select_from_ts_code_pool(10)
    # print(code_list)
    # count = 0
    # for code in code_list:
    #     df = get_dataframe_from_code(code)
    #     df.to_pickle(r'C:\Users\cyg\Desktop\test\df_{}'.format(count))
    #     count += 1
    back_test()
