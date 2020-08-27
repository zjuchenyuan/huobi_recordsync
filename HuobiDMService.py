#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Date    : 20180917
# @Author  : zhaobo
# @github  : https://github.com/huobiapi/Futures-Python-demo/blob/master/REST-Python3.5-demo/HuobiDMService.py

# zjuchenyuan: 增加了永续合约swap部分函数，文档: https://huobiapi.github.io/docs/coin_margined_swap/v1/cn/

from HuobiDMUtil import http_get_request, api_key_post, api_key_get

def create_swap_post_function(name):
    def func(self, **kwargs):
        return api_key_post(self.url, "/swap-api/v1/"+name, kwargs, self.access_key, self.secret_key)
    return func

def create_spot_get_function(name):
    def func(self, **kwargs):
        return api_key_get(self.url, name, kwargs, self.access_key, self.secret_key)
    return func

def create_spot_post_function(name):
    def func(self, **kwargs):
        return api_key_post(self.url, name, kwargs, self.access_key, self.secret_key)
    return func

class HuobiSPOT:
    
    def __init__(self,url,access_key,secret_key):
        self.url = url
        self.access_key = access_key
        self.secret_key = secret_key
    
    order_orders = create_spot_get_function("/v1/order/orders")
    """
    搜索历史订单，只能搜索一个币种，可以用start-date和end-date每次2天遍历
    states必填： submitted 已提交, partial-filled 部分成交, partial-canceled 部分成交撤销, filled 完全成交, canceled 已撤销，created
    返回：id, amount, created-at, field-amount, field-cash-amount, field-fees, price, state, symbol, type
    """
    
    order_history_48h = create_spot_get_function("/v1/order/history")
    """
    搜索最近48小时内历史订单
    start-time小于当前48h无效
    size: 1000
    """
    
    def getallcoins(self):
        """
        返回所有交易对如btcusdt
        """
        return [i["symbol"] for i in http_get_request(self.url+"/v1/common/symbols", {})["data"]]
    
    def order_matchresults(self, id):
        return api_key_get(self.url, "/v1/order/orders/"+str(id)+"/matchresults", {}, self.access_key, self.secret_key)

    subuser_list = create_spot_get_function("/v2/sub-user/user-list")
    """
    获取子用户列表
    """

    subuser_transfer = create_spot_post_function("/v1/subuser/transfer")
    """
    母子用户之间资产划转
    
    sub-uid 必填
    currency usdt
    amount
    type master-transfer-out master-transfer-in
    """
    
    account_transer = create_spot_post_function("/v1/account/transfer")

class HuobiDM:

    def __init__(self,url,access_key,secret_key):
        self.url = url
        self.access_key = access_key
        self.secret_key = secret_key

    
    '''
    ======================
    Market data API
    ======================
    '''
    
    
    # 获取合约信息
    def get_contract_info(self, symbol='', contract_type='', contract_code=''):
        """
        参数名称         参数类型  必填    描述
        symbol          string  false   "BTC","ETH"...
        contract_type   string  false   合约类型: this_week:当周 next_week:下周 quarter:季度
        contract_code   string  false   BTC181228
        备注：如果contract_code填了值，那就按照contract_code去查询，如果contract_code 没有填值，则按照symbol+contract_type去查询
        """
        params = {}
        if symbol:
            params['symbol'] = symbol
        if contract_type:
            params['contract_type'] = contract_type
        if contract_code:
            params['contract_code'] = contract_code
    
        url = self.url + '/api/v1/contract_contract_info'
        return http_get_request(url, params)
    
    
    # 获取合约指数信息
    def get_contract_index(self, symbol):
        """
        :symbol    "BTC","ETH"...
        """
        params = {'symbol': symbol}
    
        url = self.url + '/api/v1/contract_index'
        return http_get_request(url, params)
    
    
    # 获取合约最高限价和最低限价
    def get_contract_price_limit(self, symbol='', contract_type='', contract_code=''):
        """
        :symbol          "BTC","ETH"...
        :contract_type   合约类型: this_week:当周 next_week:下周 quarter:季度
        "contract_code   BTC180928
        备注：如果contract_code填了值，那就按照contract_code去查询，如果contract_code 没有填值，则按照symbol+contract_type去查询
        """
        params = {}
        if symbol:
            params['symbol'] = symbol
        if contract_type:
            params['contract_type'] = contract_type
        if contract_code:
            params['contract_code'] = contract_code
    
        url = self.url + '/api/v1/contract_price_limit'
        return http_get_request(url, params)
    
    
    # 获取当前可用合约总持仓量
    def get_contract_open_interest(self, symbol='', contract_type='', contract_code=''):
        """
        :symbol          "BTC","ETH"...
        :contract_type   合约类型: this_week:当周 next_week:下周 quarter:季度
        "contract_code   BTC180928
        备注：如果contract_code填了值，那就按照contract_code去查询，如果contract_code 没有填值，则按照symbol+contract_type去查询
        """
        params = {'symbol': symbol,
                  'contract_type': contract_type,
                  'contract_code': contract_code}
    
        url = self.url + '/api/v1/contract_open_interest'
        return http_get_request(url, params)   
        
    
    # 获取行情深度
    def get_contract_depth(self, symbol, type):
        """
        :param symbol:   BTC_CW, BTC_NW, BTC_CQ , ...
        :param type: 可选值：{ step0, step1, step2, step3, step4, step5 （合并深度0-5）；step0时，不合并深度 }
        :return:
        """
        params = {'symbol': symbol,
                  'type': type}
    
        url = self.url + '/market/depth'
        return http_get_request(url, params)
    
    # 获取永续合约行情深度数据
    def get_swap_depth(self, contract_code, type):
        params = {'contract_code': contract_code,
                  'type': type}
    
        url = self.url + '/swap-ex/market/depth'
        return http_get_request(url, params)
    
    # 获取KLine
    def get_contract_kline(self, symbol, period, size=150):
        """
        :param symbol  BTC_CW, BTC_NW, BTC_CQ , ...
        :param period: 可选值：{1min, 5min, 15min, 30min, 60min, 4hour, 1day, 1week, 1mon }
        :param size: [1,2000]
        :return:
        """
        params = {'symbol': symbol,
                  'period': period}
        if size:
            params['size'] = size
    
        url = self.url + '/market/history/kline'
        return http_get_request(url, params)
    
    
    # 获取聚合行情
    def get_contract_market_merged(self, symbol):
        """
        :symbol     "BTC_CW","BTC_NW", "BTC_CQ" ...
        """
        params = {'symbol': symbol}
    
        url = self.url + '/market/detail/merged'
        return http_get_request(url, params)
    
    
    # 获取市场最近成交记录
    def get_contract_trade(self, symbol, size=1):
        """
        :param symbol: 可选值：{ BTC_CW, BTC_NW, BTC_CQ, etc. }
        :return:
        """
        params = {'symbol': symbol,
                  'size' : size}
    
        url = self.url + '/market/trade'
        return http_get_request(url, params)
    
    
    # 批量获取最近的交易记录
    def get_contract_batch_trade(self, symbol, size=1):
        """
        :param symbol: 可选值：{ BTC_CW, BTC_NW, BTC_CQ, etc. }, size: int
        :return:
        """
        params = {'symbol': symbol,
                  'size' : size}
    
        url = self.url + '/market/history/trade'
        return http_get_request(url, params)
    
    
    
    
    
    
    '''
    ======================
    Trade/Account API
    ======================
    '''
    
    # 获取用户账户信息
    def get_contract_account_info(self, symbol=''):
        """
        :param symbol: "BTC","ETH"...如果缺省，默认返回所有品种
        :return:
        """
        
        params = {}
        if symbol:
            params["symbol"] = symbol
    
        request_path = '/api/v1/contract_account_info'
        return api_key_post(self.url, request_path, params, self.access_key, self.secret_key)
    
    
    # 获取用户持仓信息
    def get_contract_position_info(self, symbol=''):
        """
        :param symbol: "BTC","ETH"...如果缺省，默认返回所有品种
        :return:
        """
        
        params = {}
        if symbol:
            params["symbol"] = symbol
    
        request_path = '/api/v1/contract_position_info'
        return api_key_post(self.url, request_path, params, self.access_key, self.secret_key)
    
    
    
    # 合约下单
    def send_contract_order(self, symbol, contract_type, contract_code, 
                            client_order_id, price,volume,direction,offset,
                            lever_rate,order_price_type):
        """
        :symbol: "BTC","ETH"..
        :contract_type: "this_week", "next_week", "quarter"
        :contract_code: "BTC181228"
        :client_order_id: 客户自己填写和维护，这次一定要大于上一次
        :price             必填   价格
        :volume            必填  委托数量（张）
        :direction         必填  "buy" "sell"
        :offset            必填   "open", "close"
        :lever_rate        必填  杠杆倍数
        :order_price_type  必填   "limit"限价， "opponent" 对手价
        备注：如果contract_code填了值，那就按照contract_code去下单，如果contract_code没有填值，则按照symbol+contract_type去下单。
        :
        """
        
        params = {"price": price,
                  "volume": volume,
                  "direction": direction,
                  "offset": offset,
                  "lever_rate": lever_rate,
                  "order_price_type": order_price_type}
        if symbol:
            params["symbol"] = symbol
        if contract_type:
            params['contract_type'] = contract_type
        if contract_code:
            params['contract_code'] = contract_code
        if client_order_id:
            params['client_order_id'] = client_order_id
    
        request_path = '/api/v1/contract_order'
        return api_key_post(self.url, request_path, params, self.access_key, self.secret_key)
    
    
    
    # 合约批量下单
    def send_contract_batchorder(self, orders_data):
        """
        orders_data: example:
        orders_data = {'orders_data': [
               {'symbol': 'BTC', 'contract_type': 'quarter',  
                'contract_code':'BTC181228',  'client_order_id':'', 
                'price':1, 'volume':1, 'direction':'buy', 'offset':'open', 
                'leverRate':20, 'orderPriceType':'limit'},
               {'symbol': 'BTC','contract_type': 'quarter', 
                'contract_code':'BTC181228', 'client_order_id':'', 
                'price':2, 'volume':2, 'direction':'buy', 'offset':'open', 
                'leverRate':20, 'orderPriceType':'limit'}]}    
            
        Parameters of each order: refer to send_contract_order
        """
        
        params = orders_data
        request_path = '/api/v1/contract_batchorder'
        return api_key_post(self.url, request_path, params, self.access_key, self.secret_key)
    
    
    # 撤销订单
    def cancel_contract_order(self, symbol, order_id='', client_order_id=''):
        """
        参数名称          是否必须 类型     描述
        symbol           true   string  BTC, ETH, ...
        order_id             false  string  订单ID（ 多个订单ID中间以","分隔,一次最多允许撤消50个订单 ）
        client_order_id  false  string  客户订单ID(多个订单ID中间以","分隔,一次最多允许撤消50个订单)
        备注： order_id 和 client_order_id都可以用来撤单，同时只可以设置其中一种，如果设置了两种，默认以order_id来撤单。
        """
        
        params = {"symbol": symbol}
        if order_id:
            params["order_id"] = order_id
        if client_order_id:
            params["client_order_id"] = client_order_id  
    
        request_path = '/api/v1/contract_cancel'
        return api_key_post(self.url, request_path, params, self.access_key, self.secret_key)
    
    # 全部撤单
    def cancel_all_contract_order(self, symbol):
        """
        symbol: BTC, ETH, ...
        """
        
        params = {"symbol": symbol}
    
        request_path = '/api/v1/contract_cancelall'
        return api_key_post(self.url, request_path, params, self.access_key, self.secret_key)
    
    
    # 获取合约订单信息
    def get_contract_order_info(self, symbol, order_id='', client_order_id=''):
        """
        参数名称            是否必须    类型        描述
        symbol          true    string  BTC, ETH, ...
        order_id            false   string  订单ID（ 多个订单ID中间以","分隔,一次最多允许查询20个订单 ）
        client_order_id false   string  客户订单ID(多个订单ID中间以","分隔,一次最多允许查询20个订单)
        备注：order_id和client_order_id都可以用来查询，同时只可以设置其中一种，如果设置了两种，默认以order_id来查询。
        """
        
        params = {"symbol": symbol}
        if order_id:
            params["order_id"] = order_id
        if client_order_id:
            params["client_order_id"] = client_order_id  
    
        request_path = '/api/v1/contract_order_info'
        return api_key_post(self.url, request_path, params, self.access_key, self.secret_key)
    
    
    # 获取合约订单明细信息
        
    def get_contract_order_detail(self, symbol, order_id, order_type, created_at, page_index=None, page_size=None):
        """
        参数名称     是否必须  类型    描述
        symbol      true        string "BTC","ETH"...
        order_id    true        long       订单id
        order_type  true    int    订单类型。1:报单， 2:撤单， 3:爆仓， 4:交割
        created_at  true    number 订单创建时间
        page_index  false   int    第几页,不填第一页
        page_size   false   int    不填默认20，不得多于50
        """
        
        params = {"symbol": symbol,
                  "order_id": order_id,
                  "order_type": order_type,
                  "created_at": created_at}
        if page_index:
            params["page_index"] = page_index
        if page_size:
            params["page_size"] = page_size  
    
        request_path = '/api/v1/contract_order_detail'
        return api_key_post(self.url, request_path, params, self.access_key, self.secret_key)
    
    
    # 获取合约当前未成交委托
    def get_contract_open_orders(self, symbol=None, page_index=None, page_size=None):
        """
        参数名称     是否必须  类型   描述
        symbol      false   string "BTC","ETH"...
        page_index  false   int    第几页,不填第一页
        page_size   false   int    不填默认20，不得多于50
        """
        
        params = {}
        if symbol:
            params["symbol"] = symbol
        if page_index:
            params["page_index"] = page_index
        if page_size:
            params["page_size"] = page_size  
    
        request_path = '/api/v1/contract_openorders'
        return api_key_post(self.url, request_path, params, self.access_key, self.secret_key)
    
    
    # 获取合约历史委托
    def get_contract_history_orders(self, symbol, trade_type, type, status, create_date,
                                    page_index=None, page_size=None):
        """
        参数名称     是否必须  类型     描述        取值范围
        symbol      true        string  品种代码  "BTC","ETH"...
        trade_type  true        int     交易类型  0:全部,1:买入开多,2: 卖出开空,3: 买入平空,4: 卖出平多,5: 卖出强平,6: 买入强平,7:交割平多,8: 交割平空
        type        true        int     类型     1:所有订单、2：结束汏订单
        status      true        int     订单状态  0:全部,3:未成交, 4: 部分成交,5: 部分成交已撤单,6: 全部成交,7:已撤单
        create_date true        int     日期     7，90（7天或者90天）
        page_index  false   int     页码，不填默认第1页     
        page_size   false   int     不填默认20，不得多于50
        """
        
        params = {"symbol": symbol,
                  "trade_type": trade_type,
                  "type": type,
                  "status": status,
                  "create_date": create_date}
        if page_index:
            params["page_index"] = page_index
        if page_size:
            params["page_size"] = page_size  
    
        request_path = '/api/v1/contract_hisorders'
        return api_key_post(self.url, request_path, params, self.access_key, self.secret_key)

    swap_financial_record = create_swap_post_function("swap_financial_record")
    """
    查询用户财务记录
    #contract_code, type, create_date, page_index, page_size
    type: 平多：3，平空：4，开仓手续费-吃单：5，开仓手续费-挂单：6，平仓手续费-吃单：7，平仓手续费-挂单：8，交割平多：9，交割平空：10，交割手续费：11，强制平多：12，强制平空：13，从币币转入：14，转出至币币：15，结算未实现盈亏-多仓：16，结算未实现盈亏-空仓：17，穿仓分摊：19，系统：26，活动奖励：28，返利：29，资金费-收入：30，资金费-支出：31, 转出到子账号合约账户: 34, 从子账号合约账户转入:35, 转出到母账号合约账户: 36, 从母账号合约账户转入: 37
    """
    
    swap_position_info = create_swap_post_function("swap_position_info")
    """
    获取用户持仓信息
    默认返回所有合约
    """
    
    swap_sub_account_list = create_swap_post_function("swap_sub_account_list")
    """
    查询母账户下所有子账户资产信息
    """
    
    swap_order = create_swap_post_function("swap_order")
    """
    合约交易
    contract_code 如BTC-USD
    client_order_id long 可以不填
    price 价格
    volume 张数
    direction "buy"买 "sell"卖
    offset "open"开 "close"平 我们要开空用sell open
    lever_rate 1
    order_price_type limit限价 opponent对手价（不用传price）
    """
    
    swap_order_info = create_swap_post_function("swap_order_info")
    """
    获取合约订单信息
    """
