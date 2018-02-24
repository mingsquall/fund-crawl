import jieba
import time
import jieba.posseg as pseg
import pandas as pd
import numpy as np
from datetime import datetime
from snownlp import SnowNLP
import matplotlib.pyplot as plt
from datetime import datetime
from multiprocessing import Pool

def pre_data():
    comment_dataframe = pd.read_pickle("comment_dataframe")
    tradingcodes = list(set(comment_dataframe['tradingcode']))
    return comment_dataframe, tradingcodes

def gen_sentiment(row):
    sentiments = SnowNLP(row['comment']).sentiments
    return sentiments

def multi_process(df):
    try:
        df.loc[:, 'sentiments'] = df.apply(gen_sentiment, axis=1)
        return df
    except Exception as e:
        print('apply error : {0}.'.format(e))

def calc_sentiment():
    comment_dataframe, tradingcodes = pre_data()
    comment_batch = [comment_dataframe[comment_dataframe['tradingcode']==str(i)] for i in tradingcodes]
    with Pool(processes=4) as pool:
        one_df = pool.map(multi_process, comment_batch)
        sentiment_dataframe = pd.concat(one_df)
    sentiment_dataframe.to_pickle('sentiment_dataframe')
    return sentiment_dataframe

def trans_time(df):
    fund_comment = df.reset_index()
    fund_comment = fund_comment.rename(columns={'level_0': 'user', 'level_1': 'time'})
    fund_comment = fund_comment.set_index('time')
    fund_comment.index = [pd.to_datetime(time.strftime('%Y-%m-%d')) for time in fund_comment.index]  # index转为年月日格式重新赋值
    fund_comment.index.name = 'time'
    return fund_comment

def calc_sentiment_mean(df, tradingcode='110011'):
    """e.g. 110011"""
    fund_comment = df[df['tradingcode']==tradingcode]
    sentiment_mean = fund_comment['sentiment'].groupby('time').mean().iloc[-120:]
    plt.figure(figsize=(10, 6), dpi=80)
    plt.plot(sentiment_mean, label='易方达中小盘混合(110011)')
    plt.legend(loc='upper right')
    plt.xlabel('日期')
    plt.ylabel('情感值')
    plt.title('情感均值变化情况')
    plt.show()

def calc_sentiment_mov(df, tradingcode='110011', ma=7):
    """e.g. 110011"""
    fund_comment = df[df['tradingcode']==tradingcode]
    sentiment_mean = fund_comment['sentiment'].groupby('time').mean().iloc[-120:]
    sentiment_mean['mov_7'] = np.round(sentiment_mean.rolling(center=False, window=ma).mean(), 6)
    sentiment_mov_7 = sentiment_mean['mov_7']
    sentiment_mov_7 = sentiment_mov_7.dropna()
    plt.figure(figsize=(10, 6), dpi=80)
    plt.plot(sentiment_mov_7, label='易方达中小盘混合(110011)')
    plt.legend(loc='upper right')
    plt.xlabel('日期')
    plt.ylabel('情感值均值的7天移动均值')
    plt.title('情感值均值的7天移动均值的变化情况')
    plt.show()

if __name__ == '__main__':
    # 1 计算情感值
    sentiment_dataframe = calc_sentiment()
    # 2 处理时间索引
    fund_comment = trans_time(sentiment_dataframe)
    # 3 计算分组情感均值，绘图观察
    calc_sentiment_mean(fund_comment)

