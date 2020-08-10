# huobi_recordsync
Sync your huobi financial records to MySQL database

火币只会显示最近三个月的财务记录，所以有必要将这部分数据同步到数据库，另外还能方便地计算[套利](https://blog.chenyuan.me/Bitcoin/)真实收益

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
mysqlstring="MYSQL_USER|MYSQL_PASSWORD|MYSQL_HOST|MYSQL_PORT|MYSQL_DB|MYSQL_TABLENAME"
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
```

第一次执行 全量同步：对所有币种查询全量财务记录

```
FULL=1 python3 myrecord.py
```

后续每天定时执行：只查询当前持仓前50条财务记录

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
