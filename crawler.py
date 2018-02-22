#coding=utf-8

import re
import os
import json
import time
import math
import logging
import requests
import copy
import pandas as pd
from lxml import etree
from datetime import datetime
from bs4 import BeautifulSoup
from multiprocessing import Pool

class Crawler(object):
	def __init__(self, home_url, fund_url):
		self.home_url = home_url
		self.fund_url = fund_url
		self.headers = {"User-Agent":"Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_2) \
			            AppleWebKit/537.36 (KHTML, like Gecko) Chrome/63.0.3239.132 Safari/537.36"}

	def get_fund_info(self, fund_url):
		"""
		从全部开放式基金列表获取基金代码、基金名称、基金简称
		:param fund_url: 开放式基金列表页url
		:return fund_dataframe: 包含基金代码、基金名称、基金简称的dataframe
		"""
		# web crawl
		try:
			r = requests.get(fund_url, self.headers)
			# 将字符串处理为正确的json格式(键值都用双引号包含)
			fund_str = r.text.split('var db=')[1]
			fund_str = fund_str.replace('chars', '"chars"')
			fund_str = fund_str.replace('count', '"count"')
			fund_str = fund_str.replace('datas', '"datas"')
			fund_str = fund_str.replace('record', '"record"')
			fund_str = fund_str.replace('pages', '"pages"')
			fund_str = fund_str.replace('curpage', '"curpage"')
			fund_str = fund_str.replace('indexsy', '"indexsy"')
			fund_str = fund_str.replace('showday', '"showday"')
			fund_str = fund_str.replace('-4.05,-4.27,-3.58,', '"-4.05","-4.27","-3.58"')
			fund_json_loaded = json.loads(fund_str)
			fund_dataframe = pd.DataFrame(fund_json_loaded['datas'])
			fund_dataframe.to_csv('raw_fund_dataframe.csv', encoding='utf-8')
			fund_dataframe.rename(columns={0:'tradingcode', 1:"fundname", 2:'fundbrief'}, inplace=True)
			fund_dataframe = fund_dataframe.loc[:,['tradingcode', 'fundname', 'fundbrief']]
			fund_dataframe = fund_dataframe.set_index('tradingcode')
			fund_dataframe.to_pickle('fund_dataframe')
			return fund_dataframe
		except Exception as e:
			logging.error('get fund list wrong, reason: {0}'.format(e))
		"""
		# local file
		try:
			fund_dataframe = pd.read_pickle('fund_dataframe_basic_info')
			return fund_dataframe
		except Exception as e:
			logging.error('get fund list from local file wrong, reason: {0}'.format(e))
		"""
	def process_comment_basic_url(self, df):
		try:
			basic_url = "http://guba.eastmoney.com/list,of"
			fund_code = df['tradingcode']
			print('processing fund : {0}'.format(fund_code))
			init_url = basic_url + str(fund_code) + ".html"
			r = requests.get(init_url, self.headers)
			soup = BeautifulSoup(r.text, 'lxml')
			# selector = etree.HTML(r.content.decode('utf-8'))
			# page_sum = selector.xpath('//div[@class="pager"]//span[@class="pagernums"]')
			data_pager = soup.find("div", class_="pager").span.get('data-pager')  # e.g.list,of161022_|4742|80|1
			article_sum = int(data_pager.split('|')[1]) # calc page_sum according to those two values
			page_split = int(data_pager.split('|')[2])
			page_sum = int(math.ceil(article_sum / page_split))
			basic_comment_url = [basic_url + str(fund_code) + '_' + str(num) + '.html' for num in range(1, page_sum + 1)]
			df['page_sum'] = page_sum
			df['basic_comment_url'] = basic_comment_url
			return df
		except Exception as e:
			logging.error('process comment basic url wrong, reason: {0}'.format(e))

	def get_comment_basic_info(self, fund_dataframe):
		"""
		依次获取基金的评论列表初始页，以及评论总页数，将所有url信息添加到basic_comment_url
		:return fund_dataframe: 包含前置基本信息及当前基础评论的信息dataframe
		"""
		fund_dataframe['tradingcode'] = fund_dataframe.index
		try:
			fund_dataframe_batch = [fund_dataframe.iloc[i] for i in range(len(fund_dataframe))]
			with Pool(processes=4) as pool:
				one_df = pool.map(self.process_comment_basic_url, fund_dataframe_batch)
				fund_dataframe = pd.DataFrame(one_df)
			fund_dataframe.to_pickle('fund_dataframe_basic_info')
			return fund_dataframe
		except Exception as e:
			logging.error('get comment url wrong, reason: {0}'.format(e))

	def get_comment_detail_url(self, fund_dataframe):
		"""
		依次获取基金每一页评论的详细url，同时得到详细评论，用户名称，发表时间，将所有信息添加到fund_comment_dataframe
		:return fund_comment_dataframe: 包含前置基本信息及当前基础评论的信息dataframe
		"""
		# web crawl
		fund_comment_dataframe = copy.deepcopy(fund_dataframe)
		fund_comment_dataframe = fund_comment_dataframe.loc[:, ['tradingcode', 'fundname']]
		# re_obj = re.compile(r"span class=\"l3\"><a href=\"(.*?)\"")
		detail_comment_url = []
		count = 0
		for fund_code in fund_dataframe.index:
			basic_comment_url =fund_dataframe.loc[fund_code, 'basic_comment_url']
			tmp_url = []
			if basic_comment_url == []:
				detail_comment_url += [tmp_url]
			else:
				for _comment_url in basic_comment_url:
					print(_comment_url)
					r = requests.get(_comment_url, self.headers)
					soup = BeautifulSoup(r.text, 'lxml')
					comment_all = soup.find_all('span', class_='l3')
					comment_all = [self.home_url + t for t in [x.a.get('href') for x in comment_all if (len([child for child in x.children]) != 3) and x.a is not None] if '/' in t]
					tmp_url += comment_all
					print()
				detail_comment_url += [tmp_url]
			count += 1
		fund_comment_dataframe.loc[:, 'detail_comment_url'] = detail_comment_url
		fund_comment_dataframe.to_pickle('fund_dataframe_detail_info')
		# local file
		# fund_comment_dataframe = pd.read_pickle('fund_dataframe_detail_info')
		return fund_comment_dataframe

	def get_comment(self, fund_comment_dataframe):
		"""
		获取每个用户以(user_name, fund_code, publish_time)为键的comments
		:param fund_comment_dataframe: 包含每一条详细评论url的dataframe
		:return: fund_comment_dataframe: 
		"""
		comment_dataframe = pd.DataFrame()
		fund_comment_dataframe = fund_comment_dataframe
		count = 0
		for fund_code in fund_comment_dataframe.index:
			time.sleep(1)
			urls = fund_comment_dataframe.loc[fund_code, 'detail_comment_url']
			print('Processing fund {2} len {1} urls {0}...'.format(urls, len(urls), fund_code))
			if urls is []:
				print('Fund {0} ignored.'.format(fund_code))
				continue
			else:
				if count % 20 == 0:
					comment_dataframe.to_pickle('comment_dataframe')
				for url in urls:
					try:
						r = requests.get(url, self.headers, timeout=1.7)
						soup = BeautifulSoup(r.text, 'lxml')
						stockcodec = soup.find("div", class_="stockcodec")
					except Exception as e:
						print('requests error : {0}.'.format(e))
						continue
					if stockcodec is None:
						continue
					try:
						comment = soup.find("div", class_="stockcodec").get_text().strip()
					except AttributeError:
						comment = 'null comment'
					try:
						user = soup.find("div", id="zwconttbn").strong.a.get_text()
					except AttributeError:
						user = 'null user'
					try:
						time_lis = soup.find("div", class_="zwfbtime").get_text().split(' ')
						comment_time = datetime.strptime(time_lis[1] + ' ' + time_lis[2], "%Y-%m-%d %H:%M:%S")
					except AttributeError:
						comment_time = 'null time'
					multi_index = pd.MultiIndex.from_tuples([(user, comment_time)])
					comment_dataframe = comment_dataframe.append(pd.DataFrame({'comment': comment,
					                                                           'tradingcode': fund_code},
					                                                            index=multi_index))
					# print('one {0}:{1}'.format(user, comment_time))
				count += 1
				print('Finished {0} \'s comment! Now {1} done.'.format(fund_code, count))
		print('All comment done!')
		comment_dataframe.to_pickle('comment_dataframe')
		return comment_dataframe

if __name__ == '__main__':

	home_url = 'http://guba.eastmoney.com'
	fund_url = 'http://fund.eastmoney.com/Data/Fund_JJJZ_Data.aspx?t=1&lx=1&letter=&gsid=&text=&sort=zdf,desc&page=1,9999&feature=|&dt=1518327716821&atfc=&onlySale=0'
	crawler = Crawler(home_url, fund_url)
	# 1 获取基金的基本信息
	fund_dataframe = crawler.get_fund_info(crawler.fund_url)
	# 2 获得基金的评论列表初始页，评论列表页数
	fund_dataframe = crawler.get_comment_basic_info(fund_dataframe)
	# 3 获取基金的详细评论url
	fund_comment_dataframe = crawler.get_comment_detail_url(fund_dataframe)
	# 4 获取基金的详细评论
	comment_dataframe = crawler.get_comment(fund_comment_dataframe)
