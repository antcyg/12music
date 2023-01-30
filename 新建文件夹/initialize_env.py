def initialize_database(sql_core):
    sql_core.creat_table('instrument', [
        'instrument_id int primary key not null',
        'instrument_name text not null',  # 股票名/期权编号
        'description text',  # 股票的一些表述
        'instrument_type',  # 股票：个股/基金 && 期权：option
        'underlying text',  # 期权正股
        'maturity datetime',  # 期权到期时间
        'strike real',  # 期权行权价
        'option_type text'  # 期权类型
    ])

    sql_core.creat_table('market', [
        'market_id int primary key not null',
        'instrument_id',
        'timestamp datetime not null',
        'bid real',
        'ask real',
        'mid real',
        'delta real',
        'gamma real',
        'thela real',
        'vega real',
        'rho real',
        'volatility real',
        'open_interest real',  # 从首日开始，正在进行中的合约数（没完成的不算）
        'volume real',  # 当日，期权交易量（没完成的不算）
        'last_price real',
        'foreign key (instrument_id) references instrument (instrument_id)'
    ])

    sql_core.creat_table('position', [
        'position_id int primary key not null',
        'instrument_id',
        'replace_position_id',
        'qty real not null',
        'startdate datetime not null',
        'enddate datetime',
        'foreign key (instrument_id) references instrument (instrument_id)',
        'foreign key (replace_position_id) references position (replace_position_id)'
    ])

    # order是关键字
    sql_core.creat_table('my_order', [
        'order_id int primary key not null',
        'instrument_id',
        'timestamp datetime not null',
        'qty real not null',
        'order_type real not null',
        'order_price real not null',
        'foreign key (instrument_id) references instrument (instrument_id)'
    ])

    sql_core.creat_table('trade', [
        'trade_id int primary key not null',
        'order_id',
        'timestamp datetime not null',
        'qty real not null',
        'price real not null',
        'reason text',
        'foreign key (order_id) references my_order (order_id)'
    ])
