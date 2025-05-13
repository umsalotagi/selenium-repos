# -*- coding: utf-8 -*-
"""
Created on Wed Aug 21 09:20:08 2024

@author: usalotagi
"""

from kiteconnect import KiteConnect
from selenium import webdriver
from selenium.webdriver.common.by import By
import time
import os


cwd = os.chdir("C:\\Users\\usalotagi\\Python\\webdriver")

token_path = "api_key.txt"
key_secret = open(token_path,'r').read().split()
kite = KiteConnect(api_key=key_secret[0])

print(kite.login_url())
# go to this url, login and get token 

data = kite.generate_session("a2WC8BhBwowQubpjcgoZdu9MzVOEeeu3", api_secret=key_secret[1])
kite.set_access_token(data["access_token"])
with open('access_token.txt', 'w') as file:
        file.write(data["access_token"])
print("request token generated successfully")
# you can automate this fully - but no need fo now

