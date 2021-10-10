import tushare as ts
import pandas as pd
import numpy as np

pd.set_option('display.max_columns', None)  # 显示所有列

START_DATE = '20160101'  # 开始日期
END_DATE = '20211010'  # 结束日期
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


def random_select_vaild_code(cur_date, amount=2):
    cur_date_str = cur_date.strftime('%Y-%m-%d')
    if len(TS_CODE_POOL) < amount:
        return None

    result = []
    temp_code_list = []
    while len(result) < amount and len(TS_CODE_POOL) > 0:
        length = len(TS_CODE_POOL)
        random_idx = np.random.randint(0, length)
        code = TS_CODE_POOL[random_idx]
        code_df = get_dataframe_from_code(code)
        if cur_date_str in code_df.index:
            result.append(code)
            TS_CODE_POOL.pop(random_idx)
        else:
            temp_code_list.append(TS_CODE_POOL.pop(random_idx))

    TS_CODE_POOL.extend(temp_code_list)
    if len(result) == amount:
        return result
    else:
        return None


def get_next_adjust_date(cur_date, code_df_dict):
    """
    获取下一个调整日
    :param cur_date: 当前日期
    :param code_df_dict: 相关股票的df字典
    """
    next_adjust_date = cur_date + pd.offsets.BMonthBegin(1)
    end_date = pd.to_datetime(END_DATE)
    if next_adjust_date > end_date:
        return None
    next_adjust_date_str = next_adjust_date.strftime('%Y-%m-%d')
    while not judge_trade_day(next_adjust_date_str, code_df_dict):
        next_adjust_date += pd.offsets.BDay(1)
        next_adjust_date_str = next_adjust_date.strftime('%Y-%m-%d')
    return next_adjust_date


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


def adjust_position(adjust_date, funds_df, code_df_dict):
    total_value = 0
    count = 0
    cur_price_dict = {}
    adjust_date_str = adjust_date.strftime('%Y-%m-%d')
    for i in range(5):
        code = funds_df.iloc[-1]['code_{}'.format(i)]
        cash = funds_df.iloc[-1]['cash_{}'.format(i)]
        position = funds_df.iloc[-1]['position_{}'.format(i)]
        code_df = code_df_dict[code]
        if adjust_date_str in code_df.index:
            cur_price = code_df.loc[adjust_date_str, 'open']
            cur_value = cash + cur_price * position
            total_value += cur_value
            cur_price_dict[i] = cur_price
            count += 1
    adjust_value = total_value / count

    for idx, cur_price in cur_price_dict.items():
        code = funds_df.iloc[-1]['code_{}'.format(idx)]
        position = funds_df.iloc[-1]['position_{}'.format(idx)]
        cash = funds_df.iloc[-1]['cash_{}'.format(idx)]
        funds_df.loc[adjust_date_str] = funds_df.iloc[-1]
        new_position = adjust_value / cur_price // 100 * 100
        new_cash = adjust_value - new_position * cur_price
        funds_df.loc[adjust_date_str, 'position_{}'.format(idx)] = new_position
        funds_df.loc[adjust_date_str, 'cash_{}'.format(idx)] = new_cash
        str_1 = '买入' if new_position - position >= 0 else '卖出'
        str_2 = '补充' if new_cash - cash >= 0 else '移出'
        print('股票：{}，持仓调整：{}{}股，资金调整：{}{}元'.format(code, str_1, abs(new_position - position), str_2,
                                                   abs(new_cash - cash)))


def alpaca_adjust(adjust_date, funds_df, code_df_dict, buy_price_dict):
    adjust_date_str = adjust_date.strftime('%Y-%m-%d')
    earn_rate_dict = {}
    cur_code_idx_dict = {}
    for i in range(5):
        code = funds_df.iloc[-1]['code_{}'.format(i)]
        cur_code_idx_dict[code] = i
        code_df = code_df_dict[code]
        if adjust_date_str in code_df.index:
            cur_price = code_df.loc[adjust_date_str, 'open']
            origin_price = buy_price_dict[code]
            earn_rate_dict[code] = (cur_price - origin_price) / origin_price
    sort_res = sorted(earn_rate_dict.items(), key=lambda x: x[1])
    change_count = 0
    change_code_list = []
    for code, earn_rate in sort_res:
        if change_count == 2:
            break
        elif earn_rate < 0.15:
            change_code_list.append(code)
            change_count += 1
    new_code_list = random_select_vaild_code(adjust_date, len(change_code_list))
    for i in range(len(change_code_list)):
        old_code = change_code_list[i]
        new_code = new_code_list[i]
        idx = cur_code_idx_dict[old_code]
        old_code_df = code_df_dict[old_code]
        new_code_df = get_dataframe_from_code(new_code)
        old_code_price = old_code_df.loc[adjust_date_str, 'open']
        old_code_cash = funds_df.iloc[-1]['cash_{}'.format(idx)]
        old_code_position = funds_df.iloc[-1]['position_{}'.format(idx)]
        old_code_value = old_code_cash + old_code_position * old_code_price
        new_code_price = new_code_df.loc[adjust_date_str, 'open']
        new_code_position = old_code_value / new_code_price // 100 * 100
        new_code_cash = old_code_value - new_code_position * new_code_price
        funds_df.loc[adjust_date_str, 'code_{}'.format(idx)] = new_code
        funds_df.loc[adjust_date_str, 'cash_{}'.format(idx)] = new_code_cash
        funds_df.loc[adjust_date_str, 'position_{}'.format(idx)] = new_code_position

        code_df_dict.pop(old_code)
        code_df_dict[new_code] = new_code_df

        print('羊驼决策开始:')
        print('{}表现不佳，被淘汰，卖出'.format(old_code))
        print('从股池中随机选择{}并购入{}股，cash:{}'.format(new_code, new_code_position, new_code_cash))



def back_test():
    col_list = []
    for i in range(INIT_AMOUNT):
        col_list.extend(['code_{}'.format(i), 'cash_{}'.format(i), 'position_{}'.format(i)])
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
    next_adjust_date = get_next_adjust_date(first_trade_date, code_df_dict)

    funds_df.loc[first_trade_date_str] = [np.nan, INIT_CASH, 0] * INIT_AMOUNT
    for idx, code in enumerate(init_code_list):
        funds_df.loc[first_trade_date_str, 'code_{}'.format(idx)] = code

    buy_price_dict = {}
    count = 0
    while count < 5 and cur_date < next_adjust_date:
        for idx, code in enumerate(init_code_list):
            code_df = code_df_dict[code]
            if funds_df.loc[first_trade_date_str, 'position_{}'.format(idx)] == 0 and cur_date_str in code_df.index:
                buy_price = code_df.loc[cur_date_str, 'open']
                position = INIT_CASH / buy_price // 100 * 100
                cash = INIT_CASH - buy_price * position
                funds_df.loc[first_trade_date_str, 'position_{}'.format(idx)] = position
                funds_df.loc[first_trade_date_str, 'cash_{}'.format(idx)] = cash
                buy_price_dict[code] = buy_price
                count += 1
        cur_date += pd.offsets.BDay(1)
        cur_date_str = cur_date.strftime('%Y-%m-%d')

    cur_adjust_count = 1
    while next_adjust_date is not None:
        cur_date = next_adjust_date
        if cur_adjust_count % 3 == 0:
            adjust_position(cur_date, funds_df, code_df_dict)
            alpaca_adjust(next_adjust_date, funds_df, code_df_dict, buy_price_dict)
            break
        adjust_position(cur_date, funds_df, code_df_dict)
        cur_adjust_count += 1
        next_adjust_date = get_next_adjust_date(cur_date, code_df_dict)
    # print(funds_df)


if __name__ == '__main__':
    # code_list = random_select_from_ts_code_pool(10)
    # print(code_list)
    # count = 0
    # for code in code_list:
    #     df = get_dataframe_from_code(code)
    #     df.to_pickle(r'C:\Users\cyg\Desktop\test\df_{}'.format(count))
    #     count += 1
    back_test()
