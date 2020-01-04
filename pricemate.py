# -*- coding: utf-8 -*-
"""
Created on Sun Dec 15 14:54:03 2019

@author: Umar Miftah Fauzi
Code based on work from:
Samuel Chan - https://github.com/onlyphantom/pricemate
Laura Fedoruk - https://towardsdatascience.com/web-scraping-basics-selenium-and-beautiful-soup-applied-to-searching-for-campsite-availability-4a8de1decac9
"""


from bs4 import BeautifulSoup
from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
from random import randint
import datetime
import time
import pandas as pd


def selenium_collecthtml(url):  # return bs4 soup from selenium, input: url
    time_delay = randint(3,6)
    # if webdriver has permission error, try restarting the computer
    driver = webdriver.Chrome(ChromeDriverManager().install())
    driver.get(url)
    time.sleep(time_delay)
    page_source =  driver.page_source
    soup = BeautifulSoup(page_source, 'lxml')
    driver.quit()
    return soup


def url_gen(depart_date):  # generate url for GMR-BD, input: depart_date
    base_url = "https://www.tiket.com/kereta-api/cari?d=GMR&dt=STATION&a=BD&at=STATION&adult=1&infant=0&date=depart_date"
    url = base_url.replace('depart_date', depart_date.strftime("%Y-%m-%d"))
    return url


def collectdata(days_after_today): # return list of dict of departs in a day
    depart_date = datetime.datetime.now() + datetime.timedelta(days=days_after_today)
    url = url_gen(depart_date)
    soup = selenium_collecthtml(url)
    timetable = soup.find_all('div', class_='train-list')
    all_departures = dict()
    i = 0
    for train_list in timetable:
        title = train_list.find('div', class_='text-train-name').text.replace("\t", "")
        tclass = train_list.find('div', class_='text-train-class').text.replace("\t", "")
        dt = train_list.find('div', class_='text-time depart').text
        at = train_list.find('div', class_='text-time arrive').text
        if at.find('+') > 0:    # if arrival date is after departure date
            days_trip = int(at[at.find('+') + 1: -1])
            arrival_date = depart_date + datetime.timedelta(days=days_trip)
            at = at[:at.find('+')]
        else:
            arrival_date = depart_date

        # check availability thru existence of price element
        price_elem = train_list.find('div', class_='text-price')
        if price_elem:
            price = price_elem.text
            seats = 99
        else:
            price = ""
            seats = 0

        if "kursi tersisa" in price:
            oprice = price
            price = oprice[:oprice.find('.') + 4]
            seats = oprice[oprice.find('.') + 4:]
        
        dic = dict(title=title, tclass = tclass, 
                   depart_date = depart_date.strftime("%Y-%m-%d"), 
                   arrival_date = arrival_date.strftime("%Y-%m-%d"), 
                   depart_time=dt, arrive_time=at, price=price, seats = seats)
        all_departures[i] = dic
        i += 1
        
    return all_departures


# return dataframe of a day of departures
def create_df(days_after_today, sort=False):
    dicr = collectdata(days_after_today)
    df = pd.DataFrame(dicr).T
    df["price"] = df["price"].str.replace("[^0-9]", "")

    if sort:
        df["depart_time"] = pd.to_datetime(df["depart_time"])
        df.sort_values("depart_time")
    return df


# return dataframe of multiple days of departures
def multiple_days_df(start_days, end_days):
    df = create_df(start_days)
    if end_days > start_days:
        for i in range(start_days + 1, end_days + 1):
            df2 = create_df(i)
            df = df.append(df2)

    return df
    

if __name__ == "__main__":
    
    # Testing / Development:
    #url = url_gen(datetime.datetime.now() + datetime.timedelta(days=5))
    # all_departures = collectdata(5)
    #df = create_df(5)
    #df = multiple_days_df(5, 10)
