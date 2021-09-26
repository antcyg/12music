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


def judge_trade_day(code_info_dict):
    for df in code_info_dict.values():
        pass


def back_test():
    # cash、buy_price、position
    info = np.array([[INIT_CASH for i in range(INIT_AMOUNT)], np.zeros(INIT_AMOUNT), np.zeros(INIT_AMOUNT)])
    # info = np.ndarray([[INIT_CASH for i in range(INIT_AMOUNT)]])

    init_code_list = random_select_from_ts_code_pool(5)
    code_info_dict = {}
    for code in init_code_list:
        df = get_dataframe_from_code(code)
        code_info_dict[code] = df

    cur_date = pd.to_datetime(START_DATE)
    print(cur_date)
    cur_date += pd.offsets.BMonthBegin()
    print(cur_date)
    cur_date += pd.offsets.BMonthBegin()
    print(cur_date)
    cur_date += pd.offsets.BMonthBegin()
    print(cur_date)
    cur_date += pd.offsets.BMonthBegin()
    print(cur_date)


if __name__ == '__main__':
    code_list = random_select_from_ts_code_pool(10)
    print(code_list)
    count = 0
    for code in code_list:
        df = get_dataframe_from_code(code)
        df.to_pickle(r'C:\Users\cyg\Desktop\test\df_{}'.format(count))
        count += 1

