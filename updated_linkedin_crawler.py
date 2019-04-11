
# coding: utf-8

# In[1]:

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
import psutil
from bs4 import BeautifulSoup

sys.setrecursionlimit(100000)

root = 'https://www.linkedin.com'
expand_btn_class = ['pv-top-card-section__summary-toggle-button pv-profile-section__card-action-bar artdeco-container-card-action-bar mt4', 
                    'pv-profile-section__card-action-bar pv-skills-section__additional-skills artdeco-container-card-action-bar',
                    'pv-profile-section__see-more-inline pv-profile-section__text-truncate-toggle link'
                ]
saved = []
visited = []
crawled = []
start = time.time()
with open('crawled.txt','r', encoding = 'utf8') as urls :
    for url in urls :
        m = re.match(r'(.+)\n', url)
        crawled.append(m.group(1))
with open('saved.txt','r', encoding = 'utf8') as urls :
    for url in urls :
        m = re.match(r'(.+)\n', url)
        if m == None :
            saved.append(url)
        else :
            saved.append(m.group(1))


# In[2]:

def Login(driver, account, password) :
    driver.get(root)
    emailElement = driver.find_element_by_id('login-email')
    emailElement.send_keys(account)
    passwordElement = driver.find_element_by_id('login-password')
    passwordElement.send_keys(password)
    passwordElement.submit()

def merge_expanded_div(original_html, expanded_div_list):
    soup = BeautifulSoup(original_html, 'html.parser')
    print(soup.encode("utf-8"))
    for i in expanded_div_list:
        soup.body.insert(len(soup.body.contents), i)
    return soup

# In[9]:

def CrawlPage(driver) :
    attach = ""
    try :
        error = driver.find_element_by_css_selector('.error-description')
        btn = driver.find_element_by_css_selector('button[class="error-action"]')
        ActionChains(driver).move_to_element(btn).perform()
        time.sleep(random.uniform(0.3,0.7))
        ActionChains(driver).click(btn).perform()
        time.sleep(random.uniform(30,60))
        print ("[+] Be Block. Wait a minute")
        return
    except NoSuchElementException :
        pass
    if driver.current_url == 'https://www.linkedin.com/in/unavailable/' :
        print("[+] Person Profile Missed")
        time.sleep(random.uniform(2,3))
        driver.back()
        time.sleep(random.uniform(2, 3))
        return
    if len(visited)%100 == 0 and len(visited) != 0:
        info = psutil.virtual_memory()
        print ("[+] Take a break. Memory Usage : {}%".format(info.percent))
        # ClearData(driver)
        time.sleep(random.uniform(150,250))
    if time.time() - start > 1080000 :
        info = psutil.virtual_memory()
        print ("[+] Take Long Break. Memory Usage : {}%".format(info.percent))
        time.sleep(random.uniform(216000, 432000))
    if driver.current_url in saved :
        if random.uniform(0, 100) <= 10 :
            attach = "Random Read "
            pass
        else :
            print ("[+] Repeat Profile. Pass")
            time.sleep(random.uniform(2, 3))
            visited.append(driver.current_url)
            CrawlAlsoView(driver, 0)
            return
    times = 0
    city = None
    while times < 3 :
        try :
            city = driver.find_element_by_css_selector('h3[class="pv-top-card-section__location t-16 t-black--light t-normal mt1 inline-block"]')
            #print("This is city.text: " + city.text)
            break
        except NoSuchElementException :
            ActionChains(driver).send_keys('\ue035').perform()
            time.sleep(random.uniform(1,2))
            times += 1
    if city is None or ("台灣" not in city.text and "臺灣" not in city.text and "Taiwan" not in city.text):
        crawled.append(driver.current_url)
        visited.append(driver.current_url)
        file = open('crawled.txt', 'a')
        file.write(driver.current_url)
        file.write("\n")
        file.close()
        print("[+] Not Taiwanese. Go Back")
        try :
            driver.back()
            time.sleep(random.uniform(1.5,2.5))
        except TimeoutException :
                print ("[+] Timeout Occurs, Refresh This Page.")
                ActionChains(driver).send_keys('\ue035').perform()
                time.sleep(random.uniform(0.5,1.5))
        return "Back"
    now = 0
    print ("[+] {} {}Crawl Page : {}".format(len(saved), attach,driver.current_url))

    ## This goes to the bottom of the page
    cycle = True
    while cycle :
        now = ScrollTo(driver, now, now + 600)
        try :
            footer = driver.find_element_by_css_selector('#footer-inner')
            cycle = False
        except NoSuchElementException :
            cycle = True
    location = footer.location
    now = ScrollTo(driver, now, location['y'])

    #print("Now is bottom, going up.")

    ## This goes to expand the static expansion
    cycle = True
    while cycle :
        cycle = False
        for c in expand_btn_class :
            try :
                btn = driver.find_element_by_css_selector('button[class="{}"]'.format(c))
                if btn.get_attribute('aria-expanded') == 'false' and btn.is_displayed() :
                    location = btn.location
                    now = ScrollTo(driver, now, location['y'])
                    time.sleep(random.uniform(0.3,0.7))
                    ActionChains(driver).move_to_element(btn).perform()
                    time.sleep(random.uniform(0.3,0.7))
                    ActionChains(driver).click(btn).perform()
                    time.sleep(random.uniform(0.3,0.7))
                    cycle = True
                else :
                    continue
            except NoSuchElementException :
                continue
            except StaleElementReferenceException :
                continue
    original_html = driver.page_source

# ===========================================
    section = driver.find_element_by_css_selector('section[class="pv-profile-section pv-accomplishments-section artdeco-container-card ember-view"]')
    sub_accomplishments_div = section.find_elements_by_css_selector('div[class="ember-view"]')
    expanded_div_list = list()

    # This goes to expand the dynamic expansion
    dynamic_expand_btn_class = "pv-accomplishments-block__expand"
    inner_expand_btn_class = "pv-profile-section__see-more-inline pv-profile-section__text-truncate-toggle link"
    cycle = True
    loop_count = 0
    while cycle :
        cycle = False
        try :
            btn = driver.find_elements_by_css_selector('button[class="{}"]'.format(dynamic_expand_btn_class))
            for i in btn:
                if 'accomplishments_expand' in i.get_attribute('data-control-name') and i.is_displayed() :
                    location = i.location
                    now = ScrollTo(driver, now, location['y'])
                    time.sleep(random.uniform(0.3,0.7))
                    ActionChains(driver).move_to_element(i).perform()
                    time.sleep(random.uniform(0.3,0.7))
                    ActionChains(driver).click(i).perform()
                    time.sleep(random.uniform(0.3,0.7))
                    expanded_div = sub_accomplishments_div[loop_count].get_attribute('innerHTML')
                    ## There are buttons inside button, the following takes care of them
                    try: 
                        inner_btn = driver.find_element_by_css_selector(('button[class="{}"]'.format(inner_expand_btn_class)))
                        if inner_btn.get_attribute('aria-expanded') == 'false' and inner_btn.is_displayed():  
                            location = inner_btn.location
                            now = ScrollTo(driver, now, location['y'])
                            time.sleep(random.uniform(0.3,0.7))
                            ActionChains(driver).move_to_element(inner_btn).perform()
                            time.sleep(random.uniform(0.3,0.7))
                            ActionChains(driver).click(inner_btn).perform()
                            time.sleep(random.uniform(0.3,0.7))
                            expanded_div = sub_accomplishments_div[loop_count].get_attribute('innerHTML')
                        else :
                            continue
                    except Exception:
                        pass
                    if expanded_div is not None:
                        expanded_div_list.append(expanded_div)
                    cycle = True
                loop_count += 1
                if loop_count == len(btn):
                    cycle = False
                else :
                    continue
        except NoSuchElementException :
            continue
        except StaleElementReferenceException :
            continue

##=====================================
    time.sleep(10)
    if expanded_div_list != []:
        #print(type(original_html))
        html_with_expansion = merge_expanded_div(original_html, expanded_div_list)
    else:
        html_with_expansion = original_html
##=====================================
        
    m = re.match(r'https://www\.linkedin\.com/in/(.+)/', driver.current_url)
    if m == None and '/in/' not in driver.current_url :
        driver.back()
        time.sleep(random.uniform(3, 4))
        CrawlPage(driver)
        return "OK"
    if driver.current_url not in saved :
        file = open('Data/{}.html'.format(m.group(1)), 'a', encoding='utf8')
        if type(html_with_expansion) == str:
            file.write(html_with_expansion)
        else:
            file.write(html_with_expansion.prettify(formatter=None))
        file.close()
        file = open('saved.txt', 'a', encoding = 'utf8')
        file.write(driver.current_url)
        file.write('\n')
        file.close()
        saved.append(driver.current_url)
    visited.append(driver.current_url)
    CrawlAlsoView(driver, now)
    return "OK"


def CrawlAlsoView(driver, now) :
    try :
        people = driver.find_elements_by_css_selector(".pv-browsemap-section__member.ember-view")
    except NoSuchElementException  :
        print ("[+] No People Also View")
        file = open('crawled.txt', 'a')
        file.write(driver.current_url)
        file.write("\n")
        file.close()
        crawled.append(driver.current_url)
        driver.back()
        time.sleep(random.uniform(3,4))
        return "No People Also View"
    amount = len(people)
    i = 0
    while i < amount :
        if i == 0 :
            start = now
        else :
            start = 0
        cycle = True
        while True:
            people = driver.find_elements_by_css_selector(".pv-browsemap-section__member.ember-view")
            if len(people) != amount :
                ActionChains(driver).send_keys('\ue035').perform()
                print ("[+] Refresh")
                time.sleep(random.uniform(20,60))
            else :
                break
        try :
            while (people[i].get_attribute('href') in visited or people[i].get_attribute('href') in crawled) and i < amount :
                i += 1
            location = people[i].location
            ScrollTo(driver, start,location['y'])
            time.sleep(random.uniform(0.3,0.7))
            ActionChains(driver).move_to_element(people[i]).perform()
            time.sleep(random.uniform(0.3,0.7))
        except IndexError :
            print ("[+] IndexError : " + str(len(people)) + "," + str(amount) + "," + str(i))
            break
        except StaleElementReferenceException :
            print ("[+] StaleElementReferenceException : " + str(len(people)) + "," + str(amount) + "," + str(i))
            break
        if i == amount :
            break
        try :
            ActionChains(driver).click(people[i]).perform()
            time.sleep(random.uniform(2.5,3))
        except TimeoutException:
            print ("[+] Timeout Occurs, Refresh This Page.")
            ActionChains(driver).send_keys('\ue035').perform()
        time.sleep(random.uniform(2,2.5))
        CrawlPage(driver)
        i += 1
    file = open('crawled.txt', 'a')
    file.write(driver.current_url)
    file.write("\n")
    file.close()
    crawled.append(driver.current_url)
    print ("[+] Finish Page : " + driver.current_url)
    try :
        driver.back()
        time.sleep(random.uniform(2.5,3))
    except TimeoutException :
            print ("[+] Timeout Occurs, Refresh This Page.")
            ActionChains(driver).send_keys('\ue035').perform()
            time.sleep(random.uniform(3,4))
    return "OK"


# In[5]:

def ScrollTo(driver, start, end) :
    now = start
    up_rate = 5
    longdelay_rate = 20
    if start < end - 220 :
        while now < end - 198 :
            now += 66
            driver.execute_script('window.scrollTo(0, {});'.format(now))
            time.sleep(random.uniform(0.005, 0.008))
            now += 66
            driver.execute_script('window.scrollTo(0, {});'.format(now))
            time.sleep(random.uniform(0.018, 0.038))
            dice = random.uniform(0, 100)
            if dice <= longdelay_rate :
                time.sleep(random.uniform(0.6, 1.2))
                longdelay_rate = 20
            else :
                time.sleep(random.uniform(0.02, 0.2))
                longdelay_rate += 10

            dice = random.uniform(0, 100)
            if dice <= up_rate :
                now -= 66
                driver.execute_script('window.scrollTo(0, {});'.format(now))
                time.sleep(random.uniform(0.005, 0.008))
                now -= 66
                driver.execute_script('window.scrollTo(0, {});'.format(now))
                time.sleep(random.uniform(0.018, 0.038))
                up_rate = 20
                time.sleep(random.uniform(0.02, 0.2))
            else :
                up_rate += 8
    else :
        while now >= end - 198 :
            if now <= 0 :
                break
            now -= 66
            driver.execute_script('window.scrollTo(0, {});'.format(now))
            time.sleep(random.uniform(0.005, 0.008))
            now -= 66
            driver.execute_script('window.scrollTo(0, {});'.format(now))
            time.sleep(random.uniform(0.018, 0.038))

            dice = random.uniform(0, 100)
            if dice <= longdelay_rate :
                time.sleep(random.uniform(0.4, 0.8))
                longdelay_rate = 20
            else :
                time.sleep(random.uniform(0.02, 0.2))
                longdelay_rate += 10

            dice = random.uniform(0, 100)
            if dice <= up_rate :
                now += 66
                driver.execute_script('window.scrollTo(0, {});'.format(now))
                time.sleep(random.uniform(0.005, 0.008))
                now += 66
                driver.execute_script('window.scrollTo(0, {});'.format(now))
                time.sleep(random.uniform(0.018, 0.038))
                up_rate = 10
                time.sleep(random.uniform(0.02, 0.2))
            else :
                up_rate += 8
    return now


# In[6]:

def ClearData(driver) :
    
    windows = driver.window_handles
    time.sleep(2)
    driver.switch_to.window(windows[1])
    time.sleep(1)
    driver.get("chrome://settings/clearBrowserData")
    time.sleep(5)
    driver.find_elements_by_css_selector("* /deep/ paper-tab")[1].click()
    time.sleep(1)
    Select(driver.find_elements_by_css_selector("* /deep/ select[id='dropdownMenu']")[2]).select_by_index(4)
    time.sleep(2)
    i = 0
    for box in driver.find_elements_by_css_selector("* /deep/ settings-checkbox") :
        if i == 6 :
            #driver.find_element_by_css_selector("* /deep/ div[slot=body]").click()
            ActionChains(driver).send_keys(Keys.END).perform()
            time.sleep(1)
        if box.get_attribute("label") == "Cookie 和其他網站資料" :
            if not box.get_attribute("checked") :
                i += 1
                continue
        else :
            if box.get_attribute("checked") :
                i += 1
                continue
        if box.is_displayed() :
            box.click()
            i += 1
    driver.find_element_by_css_selector("* /deep/ paper-button[id='clearBrowsingDataConfirm']").click()
    time.sleep(5)
    driver.switch_to.window(windows[0])


# In[ ]:

def Main() :
    links = []
    with open('url.txt','r', encoding='utf8') as urls:
        for url in urls:
            links.append(url)
    chrome_options = webdriver.ChromeOptions()
    #chrome_options.binary_location = r"C:\\Users\\ohlab\\Desktop\\linkedin_crawler_2018-master (1)\\linkedin_crawler_2018\\chromedriver.exe"
    chrome_options.add_argument('--disable-application-cache')
    chrome_options.add_argument('--disable-gpu-program-cache')
    chrome_options.add_argument('--disable-gpu-shader-disk-cache')
    driver = webdriver.Chrome("chromedriver.exe", chrome_options=chrome_options)
    
    time.sleep(10)
    driver.execute_script('''window.open("","_blank");''')
    Login(driver, '', '')
    for link in links[400:] :
        try :
            print(link)
            driver.get(link)
            time.sleep(random.uniform(1.5, 3))
            if driver.current_url == 'https://www.linkedin.com/in/unavailable/' :
                time.sleep(random.uniform(1.5, 3))
                continue
        except TimeoutException :
            print ("[+] Timeout Occurs, Refresh This Page.")
            ActionChains(driver).send_keys('\ue035').perform()
            time.sleep(random.uniform(0.5,1.5))
        CrawlPage(driver)
        visited = []
        print ('------------------------------------------------------------')
Main() 
