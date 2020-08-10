from HuobiDMService import HuobiDM
import requests, os
import threading, pymysql, warnings, time
thread_data = threading.local()

def db():
    global thread_data
    conn = pymysql.connect(user=MYSQL_USER,passwd=MYSQL_PASSWORD,host=MYSQL_HOST,port=MYSQL_PORT,db=MYSQL_DB ,charset='utf8',init_command="set NAMES utf8mb4", use_unicode=True)
    thread_data.__dict__["conn"] = conn
    return conn

def runsql(sql, *args, onerror='raise', returnid=False, allow_retry=True):
    global thread_data
    conn = thread_data.__dict__.get("conn")
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

class Huobi_RecordSaver():
    def __init__(self, name, ID, KEY, MYSQLCONF):
        global MYSQL_USER, MYSQL_PASSWORD, MYSQL_HOST, MYSQL_PORT, MYSQL_DB, MYSQL_TABLENAME
        self.name = name
        self.dm = HuobiDM('https://api.hbdm.com', ID, KEY)
        MYSQL_USER, MYSQL_PASSWORD, MYSQL_HOST, MYSQL_PORT, MYSQL_DB, MYSQL_TABLENAME = MYSQLCONF.split("|")
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
        global MYSQL_TABLENAME
        if not records:
            return
        items = []
        sql = "insert ignore into "+MYSQL_TABLENAME+"(id,name,contract_code,type,ts,symbol,amount) values "
        for item in records:
            sql += "(" + ("%s,"*len(item))[:-1] + "),"
            items.extend(item)
        return runsql(sql[:-1], *items)

if __name__ == "__main__":
    from config import accounts, mysqlstring
    FULLFETCH = os.environ.get("FULL", False)
    for name, (HUOBIAPI_ID, HUOBIAPI_SECRET) in accounts.items():
        x = Huobi_RecordSaver(name, HUOBIAPI_ID, HUOBIAPI_SECRET, mysqlstring)
        for symbol in (x.getalllist() if FULLFETCH else x.getholdlist()):
            r=x.getrecord(symbol, full=FULLFETCH)
            print(name, symbol, "len:", len(r))
            x.saverecord(r)