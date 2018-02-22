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
- TODO
