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

def remove_nonnumeric(string):
    if isinstance(string, str):
        string = ''.join(filter(lambda x: x.isdigit(), string))
    return string

def depart_date_gen(days_after_today):
    return datetime.datetime.now() + datetime.timedelta(days=days_after_today)


def url_gen(days_after_today):  # generate url for GMR-BD, input: depart_date
    depart_date = depart_date_gen(days_after_today)
    base_url = "https://www.tiket.com/kereta-api/cari?d=GMR&dt=STATION&a=BD&at=STATION&adult=1&infant=0&date=depart_date"
    url = base_url.replace('depart_date', depart_date.strftime("%Y-%m-%d"))
    return url


def selenium_collecthtml(driver, url):  # return bs4 soup from input url
    time_delay = randint(3, 6)
    driver.get(url)
    time.sleep(time_delay)
    page_source = driver.page_source
    soup = BeautifulSoup(page_source, 'lxml')
    return soup


def price_extract(train_list): # extract price and seats from a single ticket's soup
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

    price = remove_nonnumeric(price)
    seats = remove_nonnumeric(seats)
    return price, seats


def arrival_date_extract(train_list, depart_date):
    at = train_list.find('div', class_='text-time arrive').text
    if at.find('+') > 0:    # if arrival date is after departure date
        days_trip = int(at[at.find('+') + 1: -1])
        arrival_date = depart_date + datetime.timedelta(days=days_trip)
        at = at[:at.find('+')]
    else:
        arrival_date = depart_date
    
    return arrival_date, at


def collectdata(soup, days_after_today):  # return dataframe of train tickets from bs4 soup input
    depart_date = depart_date_gen(days_after_today)
    timetable = soup.find_all('div', class_='train-list')
    all_departures = dict()
    i = 0
    for train_list in timetable:
        title = train_list.find('div', class_='text-train-name').text.replace("\t", "")
        tclass = train_list.find('div', class_='text-train-class').text.replace("\t", "")
        dt = train_list.find('div', class_='text-time').text
        arrival_date, at = arrival_date_extract(train_list, depart_date)
        price, seats = price_extract(train_list)
        
        dic = dict(title=title, tclass=tclass,
                   depart_date=depart_date.strftime("%Y-%m-%d"), 
                   arrival_date=arrival_date.strftime("%Y-%m-%d"), 
                   depart_time=dt, arrival_time=at, price=price, seats=seats)
        all_departures[i] = dic
        i += 1
    
    df = pd.DataFrame(all_departures).T
    return df


# return dataframe of multiple days of departures
def multiple_days_df(start_days, end_days):
    # open driver
    end_days = end_days + 1
    driver = webdriver.Chrome(ChromeDriverManager().install())
    for i in range(start_days, end_days):
        # pass driver & start/end days to soup generator
        url = url_gen(i)
        soup = selenium_collecthtml(driver, url)
        
        # pass soup to df generator
        df_thisday = collectdata(soup, i)
        
        # append to last df or create df
        if i == start_days:
            df = df_thisday
        else:
            df = df.append(df_thisday)
        # quit driver
    
    return df
    

if __name__ == "__main__":
    
    # Testing / Development:
    #url = url_gen(datetime.datetime.now() + datetime.timedelta(days=5))
    # all_departures = collectdata(5)
    #df = create_df(5)
    # df = multiple_days_df(0, 0)
    df = multiple_days_df(1, 3)
    # df = multiple_days_df(2, 4)