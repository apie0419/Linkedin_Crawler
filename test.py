from selenium import webdriver
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import *
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.proxy import *
from selenium.webdriver.support.select import Select
import random
import time
import re
import sys

driver = webdriver.Chrome("chromedriver.exe")
driver.get("chrome://settings/clearBrowserData")
time.sleep(5)
with open("test.txt", "w+", encoding = "utf-8-sig") as f :
    f.write(driver.page_source)

print (driver.find_elements_by_css_selector("* /deep/ paper-tab"))
driver.find_elements_by_css_selector("* /deep/ paper-tab")[1].click()
time.sleep(1)
Select(driver.find_elements_by_css_selector("* /deep/ select[id='dropdownMenu']")[2]).select_by_index(4)
time.sleep(2)
i = 0

for box in driver.find_elements_by_css_selector("* /deep/ settings-checkbox") :
    print (box.get_attribute("label"))
    if i == 6 :
        #driver.find_element_by_css_selector("* /deep/ div[slot=body]").click()
        ActionChains(driver).send_keys(Keys.END).perform()
        time.sleep(2)
    if box.get_attribute("label") == "Cookie 和其他網站資料" :
        if not box.get_attribute("checked") :
            i += 1
            continue
        print ("YES")
    else :
        #print (box.get_attribute("label"))
        if box.get_attribute("checked") :
            print ("YES")
            i += 1
            continue
    if box.is_displayed() :
        print ("Click")
        box.click()
        i += 1
    time.sleep(2)
driver.find_element_by_css_selector("* /deep/ paper-button[id='clearBrowsingDataConfirm']").click()