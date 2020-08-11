#!/usr/bin/python3
from HuobiDMService import HuobiDM, HuobiSPOT
import requests, os, sys, threading, pymysql, warnings, time
from pprint import pprint
from decimal import Decimal
thread_data = threading.local()

def db():
    global thread_data
    conn = pymysql.connect(user=MYSQL_USER,passwd=MYSQL_PASSWORD,host=MYSQL_HOST,port=MYSQL_PORT,db=MYSQL_DB ,charset='utf8',init_command="set NAMES utf8mb4", use_unicode=True)
    thread_data.__dict__["conn"] = conn
    return conn

def runsql(sql, *args, onerror='raise', returnid=False, allow_retry=True):
    global thread_data
    conn = thread_data.__dict__.get("conn")
    if len(args)==1 and isinstance(args[0], list):
        args = args[0]
    if not conn:
        conn = db()
    if not conn.open:
        conn = db()
    cur = conn.cursor()
    try:
        conn.ping()
    except:
        print("conn.ping() failed, reconnect")
        conn = db()
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            cur.execute(sql, args)
    except pymysql.err.OperationalError as e:
        conn.commit()
        cur.close()
        if allow_retry and ("Lost connection to MySQL" in str(e) or "MySQL server has gone away" in str(e)):
            conn.close()
            conn = db()
            return runsql(sql, *args, onerror=onerror, returnid=returnid, allow_retry=False)
        else:
            raise
    except:
        conn.commit()
        cur.close()
        if onerror=="ignore":
            return False
        else:
            raise
    if returnid:
        cur.execute("SELECT LAST_INSERT_ID();")
        result = list(cur)[0][0]
    else:
        result = list(cur)
    conn.commit()
    cur.close()
    return result

from pprint import pprint
#pprint(dm.swap_financial_record(contract_code="IOTA-USD",page_size=50))
#pprint(dm.swap_position_info())
#pprint(dm.swap_sub_account_list())

recordtype={"平多":3, "平空":4, "开仓手续费-吃单":5, "开仓手续费-挂单":6, "平仓手续费-吃单":7, "平仓手续费-挂单":8, "交割平多":9, "交割平空":10, "交割手续费":11, "强制平多":12, "强制平空":13, "从币币转入":14, "转出至币币":15, "结算未实现盈亏-多仓":16, "结算未实现盈亏-空仓":17, "穿仓分摊":19, "系统":26, "活动奖励":28, "返利":29, "资金费-收入":30, "资金费-支出":31, "转出到子账号合约账户":34, "从子账号合约账户转入":35, "转出到母账号合约账户":36, "从母账号合约账户转入":37}
recordtype_id2name = {v:k for k,v in recordtype.items()}
ORDERNAMES = ["id", "symbol", "amount", "created-at", "field-amount", "field-cash-amount", "field-fees", "price", "state", "type"]
ORDERNAMES2 = ["role", "filled-fees", "filled-points"] #其中role取第0个元素即可，其余均需要求和

class Huobi_RecordSaver():
    def __init__(self, name, ID, KEY, MYSQLCONF):
        global MYSQL_USER, MYSQL_PASSWORD, MYSQL_HOST, MYSQL_PORT, MYSQL_DB
        self.name = name
        self.dm = HuobiDM('https://api.hbdm.com', ID, KEY)
        self.spot = HuobiSPOT('https://api.huobi.pro', ID, KEY)
        MYSQL_USER, MYSQL_PASSWORD, MYSQL_HOST, MYSQL_PORT, MYSQL_DB = MYSQLCONF.split("|")
        MYSQL_PORT = int(MYSQL_PORT)

    def getholdlist(self):
        # 返回当前持仓的币种
        return [i["symbol"] for i in self.dm.swap_position_info()['data']]
    
    def getalllist(self):
        # 返回所有币种
        swap_index = requests.get("https://futures.huobi.com/swap-order/x/v1/swap_index", headers={"source":"web"}).json()["data"]
        return [i["contract_code"].replace("-USD","") for i in swap_index if i["contract_code"].endswith("-USD")]
    
    def getrecord(self, symbol, full=False):
        # 返回：id, 账户名称, 合约代码, 类型, 时间戳, 币种, 数量Decimal(20,10)
        page_index = 1
        res = []
        pagedata = self.dm.swap_financial_record(contract_code=symbol+"-USD", page_size=50, page_index=page_index)["data"]
        res.extend(pagedata["financial_record"])
        if full:
            while page_index < pagedata["total_page"]:
                page_index += 1
                pagedata = self.dm.swap_financial_record(contract_code=symbol+"-USD", page_size=50, page_index=page_index)["data"]
                res.extend(pagedata["financial_record"])
        return [[i["id"], self.name, i["contract_code"], recordtype_id2name.get(i["type"], i["type"]), i["ts"], i["symbol"], i["amount"]] for i in res]

    def saverecord(self, records):
        if not records:
            return
        items = []
        sql = "insert ignore into records(id,name,contract_code,type,ts,symbol,amount) values "
        for item in records:
            sql += "(" + ("%s,"*len(item))[:-1] + "),"
            items.extend(item)
        return runsql(sql[:-1], items)

    def getspotorder_recent(self):
        # 一次API调用即可查询所有币种48h内所有订单
        # 返回：id, symbol, amount, created-at, field-amount, field-cash-amount, field-fees, price, state, type
        # 只考虑已经完成的订单，不考虑撤单
        data = self.spot.order_history_48h(size=1000)["data"]
        return [[item[i] for i in ORDERNAMES] for item in data if item["state"] in ["partial-canceled","filled"]]

    def getspotorder_full(self, coins=None, days=180):
        # 每个币种都需要调用days/2=90次API查询
        # 建议传入coins币种范围，不传则会查询所有以usdt计价的币种
        if not coins:
            coins = [i.replace("usdt","") for i in self.spot.getallcoins() if i.endswith("usdt")]
        #print(coins)
        now = int(time.time()*1000)
        res = []
        for coin in coins:
            i = -2
            for _ in range(int(days//2)):
                i+=2
                starttime = now-(i+2)*86400000
                endtime = now-i*86400000
                data = self.spot.order_orders(**{"symbol":coin+"usdt", "states":"partial-canceled,filled", "start-time":starttime, "end-time":endtime})["data"]
                print("order request:", coin, i, starttime, "len:", len(data), file=sys.stderr)
                res.extend([[item[i] for i in ORDERNAMES] for item in data])
        return res
    
    def order_getmatchdata(self, data):
        # 增加成交明细的数据
        # 还会在数据末尾添加当前的name账户名
        for item in data:
            id = item[0]
            x = self.spot.order_matchresults(id)["data"]
            print("matchresults", id, "len:", len(x), file=sys.stderr)
            role = x[0]["role"]
            fees = sum([Decimal(i["filled-fees"]) for i in x])
            points = sum([Decimal(i["filled-points"]) for i in x])
            item.extend([role, fees, points, self.name])
        return data
    
    def saveorder(self, orders):
        # 数据库里还需要存储成交信息filled-fees, role, filled-points, filled-points
        # 所以需要查询成交明细后再调用
        if not orders:
            return
        items = []
        sql = "insert ignore into orders(`"+("`,`".join(ORDERNAMES+ORDERNAMES2+["name"]))+"`) values "
        for item in orders:
            sql += "(" + ("%s,"*len(item))[:-1] + "),"
            items.extend(item)
        return runsql(sql[:-1], items)
    

if __name__ == "__main__":
    from config import accounts, mysqlstring
    FULLFETCH = os.environ.get("FULL", False)
    for name, (HUOBIAPI_ID, HUOBIAPI_SECRET) in accounts.items():
        x = Huobi_RecordSaver(name, HUOBIAPI_ID, HUOBIAPI_SECRET, mysqlstring)
        for symbol in (x.getalllist() if FULLFETCH else x.getholdlist()):
            r=x.getrecord(symbol, full=FULLFETCH)
            print(name, symbol, "len:", len(r))
            x.saverecord(r)
        orders = x.order_getmatchdata(x.getspotorder_recent())
        x.saveorder(orders)