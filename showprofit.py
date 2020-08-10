from config import accounts, mysqlstring
import requests, os
import threading, pymysql, warnings, time
sess = requests.session()
pricedata = {i["symbol"]:i["close"] for i in sess.get("https://api.huobi.pro/market/tickers").json()["data"]}
udstprice =[i for i in sess.get("https://www.huobi.com/-/x/general/exchange_rate/list").json()["data"] if i["name"]=="usdt_cny"][0]["rate"]

from myrecord import Huobi_RecordSaver, runsql

if __name__ == "__main__":
    print("USDT:",udstprice)
    name, (HUOBIAPI_ID, HUOBIAPI_SECRET) = list(accounts.items())[0]
    Huobi_RecordSaver(name, HUOBIAPI_ID, HUOBIAPI_SECRET, mysqlstring)
    sums = {}
    for name, symbol, amount in runsql("SELECT name,symbol, SUM(amount) FROM `records` WHERE `type` IN ('资金费-收入', '资金费-支出') group by name,symbol"):
        cny = float(amount)*pricedata[symbol.lower()+"usdt"]*udstprice
        print(name, symbol, "%.2f"%cny, sep="\t")
        sums.setdefault(name, []).append(cny)
    print("\nSum:")
    for name, value in sums.items():
        print(name, "%.2f"%sum(value), sep="\t")