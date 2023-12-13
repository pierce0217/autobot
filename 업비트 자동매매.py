import pyupbit
import pandas as pd
from datetime import datetime
import numpy as np
import math
import time
import calendar
import asyncio
import telebot
import json
import pickle
import os

with open('C:/Users/K.H/Desktop/코딩/Keys.txt', 'r') as f:
    lines = f.readlines()
    token = lines[0].strip()
    chat_id = lines[1].strip()
    access = lines[2].strip()
    secret = lines[3].strip()
    
upbit = pyupbit.Upbit(access, secret)
bot = telebot.TeleBot(token=token)
upbit.get_balances()
last_checked_time = None
crypto_list = ["KRW-BTC","KRW-SOL","KRW-BCH","KRW-ETH"]


def telegramlog(message):
    print(datetime.now().strftime('[%y/%m/%d %H:%M:%S]'), message)
    strbuf = datetime.now().strftime('[%y/%m/%d %H:%M:%S] ') + message
    bot.send_message(chat_id, text = strbuf)


def printlog(message, *args):
    print(datetime.now().strftime('[%y/%m/%d %H:%M:%S]'), message, *args)

def get_candle_high_low_range(crypto):
    df = pyupbit.get_ohlcv(crypto, interval = 'minute240', to=datetime.now()).tail(20)
    candle_high = max(df['high'])
    candle_low = min(df['low'])
    candle_high80 = candle_low + 0.8 * (candle_high - candle_low)
    candle_low20 = candle_low + 0.2 * (candle_high - candle_low)   
    return candle_high, candle_low, candle_high80, candle_low20

def buy_crypto(crypto):
    current_price = pyupbit.get_current_price(crypto)
    unit = upbit.get_balance(ticker=crypto)
    if current_price > get_candle_high_low_range(crypto)[2] and str(unit)=='0':
        krw = upbit.get_balance(ticker="KRW")
        orderbook = pyupbit.get_orderbook(ticker=crypto)['orderbook_units'][0]['ask_price']
        amount = krw / (1 + len(crypto_list) - len(upbit.get_balances())) - 0.01 * krw
        unit = amount / orderbook
        upbit.buy_market_order(crypto, amount)
        telegramlog("BUY ORDER SUBMITTED: "+str(amount)+" "+str(crypto))


def sell_crypto(crypto):
    current_price = pyupbit.get_current_price(crypto)
    unit = upbit.get_balance(ticker=crypto)
    if current_price < get_candle_high_low_range(crypto)[3] and str(unit) != '0':
        upbit.sell_market_order(crypto, unit)
        amount = unit * current_price
        profit = round((current_price/ upbit.get_avg_buy_price(ticker=crypto) - 1) * 100,2)
        telegramlog("SELL ORDER SUBMITTED "+str(amount)+" "+str(profit)+"%"+" "+str(crypto))

def stoploss_crypto(crypto):
    current_price = pyupbit.get_current_price(crypto)
    unit = upbit.get_balance(ticker=crypto)
    if current_price < 0.91 * upbit.get_avg_buy_price(ticker=crypto) and str(unit) != '0':
        upbit.sell_market_order(crypto, unit)
        amount = unit * current_price
        telegramlog("STOP LOSS ORDER SUBMITTED "+str(amount)+" "+str(crypto))

def calculate_asset_percentage(balances):
    total_balance = sum(float(asset['balance']) * float(asset['avg_buy_price']) if float(asset['avg_buy_price']) > 0 else float(asset['balance']) for asset in balances)
    asset_percentages = {
        asset['currency']: round((float(asset['balance']) * float(asset['avg_buy_price']) / total_balance) * 100, 1) if float(asset['avg_buy_price']) > 0 else round((float(asset['balance']) / total_balance) * 100, 1) for asset in balances
    }
    asset_percentages_with_symbol = {currency: f"{percentage}%".replace(".0%", "%") for currency, percentage in asset_percentages.items()}
    return asset_percentages_with_symbol


def wait_until_top_of_hour():
    current_time = datetime.now()
    while current_time.minute != 0 and current_time.second != 0:
        time.sleep(3)  # 3초씩 대기

while True:
    try:
        buy_crypto(crypto_list[0])
        buy_crypto(crypto_list[1])
        buy_crypto(crypto_list[2])

        
        sell_crypto(crypto_list[0])
        sell_crypto(crypto_list[1])
        sell_crypto(crypto_list[2])

        
        stoploss_crypto(crypto_list[0])
        stoploss_crypto(crypto_list[1])
        stoploss_crypto(crypto_list[2])
        
        current_time = datetime.now()
        if last_checked_time is None or (current_time.minute == 0 and current_time != last_checked_time):
           balances = upbit.get_balances()
           percentages = calculate_asset_percentage(balances)
           telegramlog(f"Current balances: {percentages}")     
           last_checked_time = current_time

           # 정각까지 1분씩 대기
           wait_until_top_of_hour()
           
    except:
        print("Error! ")
        telegramlog("Bot Error!")
    
    time.sleep(1)
