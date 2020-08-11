# huobi_recordsync
Sync your huobi financial records to MySQL database

火币只会显示最近三个月的财务记录，所以有必要将这部分数据同步到数据库，另外还能方便地计算[套利](https://blog.chenyuan.me/Bitcoin/)真实收益

以及订单记录（撤单的除外），便于计算一共在币币交易支付了多少手续费

## 用法

创建API Key: 只需要读取权限 https://www.hbg.com/zh-cn/apikey/

注意到不绑定IP的密钥只有3个月有效期，最多绑定20个IP段，如果你打算用Travis CI来定时同步这个数据，我们可以简单粗暴地绑定IP段为：`0.0.0.0/1,128.0.0.0/1`

不同的子账号需要在[子账号管理页面](https://account.huobi.com/zh-cn/subaccount/management/)分别创建API Key

写入config.py:

```
accounts={
   "main": ["Access Key", "Secret Key"],
   #多个账号可以写多行 账号名main将作为name写入数据库
}
mysqlstring="MYSQL_USER|MYSQL_PASSWORD|MYSQL_HOST|MYSQL_PORT|MYSQL_DB"
```

MySQL建表：

```
CREATE TABLE `records` (
  `id` int(11) NOT NULL,
  `name` char(10) NOT NULL,
  `contract_code` char(10) DEFAULT NULL,
  `type` varchar(255) CHARACTER SET utf8 DEFAULT NULL,
  `ts` bigint(20) DEFAULT NULL,
  `symbol` char(10) DEFAULT NULL,
  `amount` decimal(20,10) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `name` (`name`),
  KEY `name_2` (`name`,`type`,`symbol`),
  KEY `type` (`type`),
  KEY `ts` (`ts`),
  KEY `symbol` (`symbol`),
  KEY `contract_code` (`contract_code`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8
CREATE TABLE `orders` (
  `id` bigint(20) NOT NULL,
  `name` char(10) DEFAULT NULL,
  `symbol` char(10) DEFAULT NULL,
  `amount` decimal(40,18) DEFAULT NULL,
  `created-at` bigint(20) DEFAULT NULL,
  `field-amount` decimal(40,18) DEFAULT NULL,
  `field-cash-amount` decimal(40,18) DEFAULT NULL,
  `field-fees` decimal(40,18) DEFAULT NULL,
  `price` decimal(40,18) DEFAULT NULL,
  `state` varchar(20) DEFAULT NULL,
  `type` varchar(20) DEFAULT NULL,
  `role` varchar(10) DEFAULT NULL,
  `filled-fees` decimal(40,18) DEFAULT NULL,
  `filled-points` decimal(40,18) DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8
```

第一次执行 全量同步：对所有币种查询全量财务记录；查询60天内main账户的所有btc和eth订单

```
FULL=1 python3 myrecord.py
python3 orders_fullfetch.py main btc,eth 60
```

后续每天定时执行：只查询当前持仓前50条财务记录，以及48小时内的币币交易订单

```
python3 myrecord.py
```

## 查询收益

查询数据库 显示账户名、币种、资金费收益 以及汇总，单位为人民币CNY

```
# python3 showprofit.py
taoli   IOTA    28.48
taoli   ONT     16.35
taoli   XTZ     0.92
taoli   ZEC     6.87

Sum:
taoli   52.62
```

当前为2020年8月10日中午12点，本金3000投入一周（6.92买入USDT），收益52.62元，当前USDT价格6.90

## 附加说明

火币自己APP用的订单查询可以查询到任意币种四个月的所有记录，但同名的开放API一次调用只能查询单个币种两天的数据，不过API可以查询到180天

也就意味着如果你参与了大量币种的交易例如100个，全量获取所有的币币交易记录需要100*180/2=9000次请求。。。

你也可以在这里查询导出到订单记录： https://www.huobi.com/zh-cn/transac/?tab=1&type=0

手续费相关说明：

- `field-fees`是这次交易的手续费，买入为币，卖出为钱 例如买入10000YEE，手续费field-fees就是20YEE
- `filled-fees`为扣除的手续费，说明此时没有开启HT抵扣，等于field-fees
- `filled-points`为抵扣的HT或点卡的数量，我这里没考虑点卡，此时filled-fees=0

如果你要查询手续费汇总，按1USDT=7RMB计算，SQL应该是这样：

```
SELECT sum(`field-fees`*`price`*7) FROM `orders`;
```

如果不考虑HT本身的价格变化，将HT当成固定成本，令1HT=30RMB，这样计算：

```
SELECT sum(`filled-fees`*`price`*7+`filled-points`*30) FROM `orders`;
```

