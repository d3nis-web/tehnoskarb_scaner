#!/usr/bin/env python3
#coding: utf-8
import os,re
import requests
from bs4 import BeautifulSoup
import json
import urllib
import time


# config =========================================================
dir_path = os.path.dirname(os.path.realpath(__file__))
with open(os.path.join(os.getcwd(),"config.json"),"r") as f:
	config_data = f.read()
CATEGORIES = json.loads(config_data)["categories"]
TELEGRAM_TOKEN = json.loads(config_data)["telegram_token"]
TELEGRAM_CHAT_ID = json.loads(config_data)["chat_id"]
TELEGRAM_TEST_CHAT_ID = json.loads(config_data)["test_chat_id"]
USER_EMAIL = ""
USER_PHONE = ""
# ================================================================

def internet_on():
	try:
		urllib.request.urlopen('https://tehnoskarb.ua', timeout=5)
		print("connection ok...")
		return True
	except Exception as e:
		print("connection fail...")
		time.sleep(1)

class Scaner:
	def __init__(self,category):
		self.products = []
		self.category = category
		self.pages = 1
		self.logfile_name = os.path.join(dir_path,"LOG_"+self.category+".txt")
		self.url = "https://tehnoskarb.ua/catalog/{}?page={}".format(self.category,self.pages)
		self.body = requests.get(self.url).text
		self.soup = BeautifulSoup(self.body,"html.parser")
		self.parse()
		if os.path.exists(self.logfile_name):
			self.check()
		with open(self.logfile_name,"w") as logfile:
			logfile.write(json.dumps(self.products))

	def reserve_products(self,new_items_urls):
		for item_url in new_items_urls:
			try:
				# get new item ids============================================
				spans = str(BeautifulSoup(requests.get(item_url).text,"html.parser").find("tbody").find_all("span"))
				new_item_ids = re.findall("[\d]+-[\d]+",spans)
				# create session==============================================
				session = requests.Session()
				form_data = {
					"email":USER_EMAIL,
					"phone":USER_PHONE,
					"redirect":"/",
					"action":"login",
				}
				session.post("https://tehnoskarb.ua/login",data=form_data)
				#=============================================================
				#add to favorite
				session.get("https://tehnoskarb.ua/share/{}/".format(re.search("\d+",item_url).group(0)))
				# add to cart ================================================
				for new_item_id in new_item_ids:
					new_item_id=new_item_id.replace("<","").replace(">","")
					# add to cart
					cart_result = session.get("https://tehnoskarb.ua/includes/ajax/ajax.basket.php?id=cart_popup&action=add&art={}".format(new_item_id)).text
					if "САМОВЫВОЗ" in cart_result:
						self.send_message(">>>>> Новый товар <<<<< {} \n {}".format(item_url,">>> НЕ ДОБАВЛЕНО В КОРЗИНУ !"))
					else:
						self.send_message(">>>>> Новый товар <<<<< {} \n {}".format(item_url,">>> ДОБАВЛЕНО В КОРЗИНУ !"))
				# =============================================================
			except Exception as e:
				print(e)
				self.send_message(">>>>> Новый товар <<<<< {} \n {}".format(i,">>> НЕ ДОБАВЛЕНО В КОРЗИНУ (ошибка) !"))

	def send_message(self,msg):
		try:
			# url = "https://api.telegram.org/bot{}/getUpdates".format(TELEGRAM_TOKEN)
			# res = json.loads(requests.get(url).text)
			send_msg_url = "https://api.telegram.org/bot{}/sendMessage?text='{}'&chat_id={}".format(TELEGRAM_TOKEN,msg,TELEGRAM_CHAT_ID)
			requests.get(send_msg_url)
			send_test_msg_url = "https://api.telegram.org/bot{}/sendMessage?text='{}'&chat_id={}".format(TELEGRAM_TOKEN,msg,TELEGRAM_TEST_CHAT_ID)
			requests.get(send_test_msg_url)
		except Exception as e:
			print(e)

	def parse(self):
		# parse and append all products to log file
		try:
			self.pages = int(self.soup.find("span",class_="cur_page").find_all("span")[-1].text.replace("/",""))
		except Exception as e:
			print(e)

		for page in range(1,self.pages+1):
			if self.pages>1:
				self.url = "https://tehnoskarb.ua/catalog/{}?page={}".format(self.category,page)
				self.body = requests.get(self.url).text
				self.soup = BeautifulSoup(self.body,"html.parser")
			items = self.soup.find("div",class_="products").find("ul").find_all("li")
			for i in items:
				try:
					data = {
							"id":re.search('catalog\/([^-]+)', i.find("a")['href']).group(1),
							"name":i.find("h4").text,
							"offers":re.search("\d+",i.find("p").text).group(),
							"url":"https://tehnoskarb.ua"+i.find("a")["href"],
							}
					self.products.append( data )
				except Exception as e:
					pass
		self.total_offers = sum([int(product["offers"]) for product in self.products])
		print("> {} - {} - {} ".format(self.category,len(self.products),self.total_offers))

	def check(self):
		print("check")
		new_items = []
		new_offers = []
		log_data = open(self.logfile_name,"r")
		json_data = json.loads(log_data.read())
		# check for new ( by id )
		for pid in [x for x in self.products]:
			if pid["id"] not in [x["id"] for x in json_data]:
				new_items.append(pid["url"])

		for r in self.products:
			for l in json_data:
				if r["id"] == l["id"]:
					if int(r["offers"])>int(l["offers"]):
						new_offers.append(r["url"])
		log_data.close()

		if new_items:
			self.reserve_products(new_items)
			print(new_items)


		if new_offers:
			self.send_message(">>>>> Новое предложение <<<<< {}".format(" , ".join(new_offers)))
			print(new_offers)





while 1:
	try:
		if internet_on():
			for i in CATEGORIES:
				Scaner(i)
		time.sleep(60)
	except Exception as e:
		print(e)
		
	
