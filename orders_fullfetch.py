from myrecord import Huobi_RecordSaver
import sys, os
if len(sys.argv)==1:
    print("Usage: python3", sys.argv[0], "<account name> <coins> <days>")
    print("Example: python3", sys.argv[0], "taoli iota,xtz 10")
    exit()

from config import accounts, mysqlstring
name = sys.argv[1]
HUOBIAPI_ID, HUOBIAPI_SECRET = accounts[name]
x = Huobi_RecordSaver(name, HUOBIAPI_ID, HUOBIAPI_SECRET, mysqlstring)
data = x.getspotorder_full(coins=[i.lower() for i in sys.argv[2].split(",")], days=int(sys.argv[3]))
data = x.order_getmatchdata(data)
x.saveorder(data)