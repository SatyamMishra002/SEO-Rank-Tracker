import os
import sys
import requests
from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service 
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
import time,datetime
from selenium.common.exceptions import TimeoutException
import re
from selenium.common.exceptions import WebDriverException
import boto3
import wx
import globalvar
import domain_country_dict
import random
app = wx.App()



# Python Codpyt
def ChromeDriver(project,country_code,Keyword):


    try:
        chrome_options = Options()
        chrome_service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=chrome_service, options=chrome_options)
        driver.maximize_window()
        site_position  = generate_report(driver,project,country_code,Keyword)
        return site_position

    except Exception as e :
        print(e.msg)


def generate_report(driver,project,country_code,Keyword):
    try:

        url = f'https://www.google.com/search?q={Keyword}&cr=country{country_code}&num=100'
        driver.get(url)
        time.sleep(2)
        captcha = driver.find_element(By.XPATH,'/html/body')
        capthca_text = captcha.get_attribute('outerHTML')
        if "I'm not a robot" in capthca_text :
            time.sleep(random.randint(5,10))
            driver.get(url)
            


        total_urls = driver.find_elements(By.XPATH,'//*[@id="rso"]/div')
        for num, result in enumerate(total_urls):
            url_words = result.get_attribute('outerHTML')
            if project in url_words:
                print(f'project at ({num+1}) position in {globalvar.country} on {datetime.date.today()}')
                return num+1
        total_urls = driver.find_elements(By.XPATH,'//*[@id="rso"]/div[2]/div')
        for num, result in enumerate(total_urls):
            url_words = result.get_attribute('outerHTML')
            if project in url_words:
                print(f'project at ({num+1}) position in {globalvar.country} on {datetime.date.today()}')
                return num+1
        return 0

        

    except Exception as e :
        print(e)    

def check_position(project, country, keyword):
    time.sleep(random.randint(5,10))
    site_position = ChromeDriver(project, country, keyword)
    return site_position


