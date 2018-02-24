import jieba
import jieba.posseg as pseg
import pandas as pd
from datetime import datetime
from snownlp import SnowNLP
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

if __name__ == '__main__':
    sentiment_dataframe = calc_sentiment()
    print(sentiment_dataframe)
