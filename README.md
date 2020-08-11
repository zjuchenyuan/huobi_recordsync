# huobi_recordsync
Sync your huobi financial records to MySQL database

火币只会显示最近三个月的财务记录，所以有必要将这部分数据同步到数据库

目前支持以下数据类型同步：
- 永续合约财务记录，能方便地计算[套利](https://blog.chenyuan.me/Bitcoin/)真实收益
- 币币现货交易订单记录（撤单的除外），便于计算一共支付了多少手续费

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
  PRIMARY KEY (`id`),
  KEY `name` (`name`),
  KEY `symbol` (`symbol`),
  KEY `created-at` (`created-at`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8
```

第一次执行 全量同步：对所有永续合约币种查询全量财务记录；查询60天内main账户的所有btc和eth订单

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

### 火币API的限制

火币自己APP用的订单查询一次调用可以查询到所有币种四个月的所有记录，
但同名的开放API一次调用只能查询单个币种两天的数据（不过API可以查询到180天）

也就意味着如果你参与了大量币种的交易例如100个，全量获取所有的币币交易记录需要`100*180/2=9000`次请求；
如果你不想自己列举币种的话，目前火币上有614个交易对，单个账户就需要55260次请求

不过提供的最近48小时API可以查到所有币种，所以还是每天定时任务一次比较简单，避免全量同步啊

### 手动导出币币交易订单

当你不记得自己交易了多少币种时（也就难以确定orders_fullfetch.py的参数），
你可以在这里查询导出订单记录： https://www.huobi.com/zh-cn/transac/?tab=1&type=0

### 手续费相关说明

- `field-fees`等价于`field-amount`*0.002，是这次交易的**抵扣前**手续费，买入为币，卖出为钱
- `filled-fees`为扣除的手续费，说明此时没有开启HT抵扣，等于field-fees
- `filled-points`为抵扣的HT或点卡的数量，我这里没考虑点卡，此时filled-fees=0
- `field-amount` 完全成交时等于下单的数量`amount`，这是扣除手续费之前的数量
- `field-cash-amount` 下单时的钱的数量 等于 amount乘以price

不开启HT抵扣：实际到账的币的数量是`field-amount`减去`filled-fees`

如果你要查询手续费汇总，只交易过USDT计价的交易对，不考虑HT抵扣的优惠，SQL应该是这样：单位是USDT

```
SELECT sum(`field-fees`*`price`) FROM `orders` where type like 'buy%';
#等价于SELECT sum(`field-amount`*0.002*`price`) FROM `orders` where type like 'buy%';
SELECT sum(`field-fees`) FROM `orders` where type like 'sell%';
```

考虑HT抵扣后，这样计算：前两项单位为USDT，后一项为HT

```
SELECT sum(`filled-fees`*`price`) FROM `orders` where type like 'buy%';
SELECT sum(`filled-fees`) FROM `orders` where type like 'sell%';
SELECT sum(`filled-points`) FROM `orders`;
```

### role

role只有两种：maker和taker。maker下订单后没有与已经存在的订单立即成交，提供了流动性；taker提取流动性，如市价单按对手价成交

在火币的普通用户币币交易，maker和taker都是相同的费率，不过在其他交易所maker甚至有负费率 [Crypto守护者@知乎：在更多负手续费的环境下交易山寨币](https://zhuanlan.zhihu.com/p/34082684)


