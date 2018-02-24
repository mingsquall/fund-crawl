# Fund Crawl
> 爬取基金基本信息以及基金评论数据。
> 仅供个人交流学习使用。

## Features
- Crawl
    - requests + BeautifulSoup + lxml
- Process
    - multiprocessing
- Data schema
    - pandas 

## Data Schema
- Fund Information
    - dataframe: `fund_dataframe_basic_info`
        - index: 
            - fundcode (基金代码)
        - columns: 
            - fundname (基金名)
            - fundbrief (基金简写)
            - tradingcode (基金代码)
            - page_sum (评论页数)
            - basic_comment_url (基金股吧的每页评论url，每个url内包含80个详细评论url)
- Fund Detail 
    - dataframe: `fund_dataframe_detail_info`
        - index:
            - fundcode (基金代码)
        - columns:
            - detail_comment_url (每条详细评论url)   

- Comment Information
    - dataframe: `comment_dataframe`
        - index: 
            - user (用户)
            - time (时间)
        - columns: 
            - comment (详细评论)
            - tradingcode (基金代码)

- 上述爬取后生成的dataframe通过pickle持久化
    - 读取数据：

```
> import pandas as pd
> df = pd.read_pickle('comment_dataframe')
> df
    		                      comment	                tradingcode
user     comment_time
婷婷0o0	2018-02-11 11:33:44	 怎么9号涨了这么多，不科学啊	005406
元牝珠	 2018-02-10 23:41:12	买了的可以跑了	            005406
..

``` 

## Data Mining
- 完成了上述数据获取，持久化后，接下来进行数据分析

- 前往查看：[基金情感分析过程](http://nbviewer.jupyter.org/github/patientman/fund-crawl/blob/master/sentiment_analyse.ipynb)
- 探索后得到情感值均值的14天移动均值的变化情况可能与基金净值的涨跌幅情况存在相关关系
    - 此处以易方达中小盘混合(110011)为例 
    - 其情感值均值的14天移动均值的变化情况如下所示：
    ![](http://7xqb68.com1.z0.glb.clouddn.com/sentiment_mov.png)
    
    - 其基金净值走势情况如下所示(摘自天天基金）：
    ![](http://7xqb68.com1.z0.glb.clouddn.com/110011.jpg)

- 粗略观察：
    - 2017年11月中下旬至12月初时，情感值均值的14天移动均值的变化趋势与基金净值走势均处在下跌状态，表现出相关性
    
    - 2018年1月中旬至2月初时，股市大跌，基金净值大跌，基金评论用户情感值也在大幅下跌，直到股市反弹，表现出相关性

    - 2018年2月上旬触底反弹，（春节前后）基金净值呈现增长趋势，评论区股友情感值整体处于增长状态

- 后续探索：
    - 由于评论基本基于散户，而散户存在追涨杀跌的能力，散户情绪也许可以作为一个阈值，在情绪疯涨到一个阈值时，及时减仓，有效规避风险，这或许可成为未来探索研究的一方向


