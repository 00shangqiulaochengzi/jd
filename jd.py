import re
from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from pyquery import PyQuery as pq
import pymongo
from config import *

client = pymongo.MongoClient(MONGODB_URL)
db = client[MONGODB_DB]
driver = webdriver.Chrome()
wait = WebDriverWait(driver, 20)


def search():
    try:
        driver.get("https://www.jd.com/")
        input = wait.until(EC.presence_of_element_located((By.ID, "key")))
        submit = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "#search > div > div.form > button")))
        input.send_keys("笔记本")
        submit.click()
        # 获取一共有多少页
        total = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "#J_bottomPage > span.p-skip > em:nth-child(1) > b")))
        get_product()
        return total.text
    # 捕捉timeout异常，并用递归的方法循环访问网页
    except TimeoutException:
        return search()

def next_page(page_number):
    try:
        # 获取选择页码的文本框和提交按钮
        input = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "#J_bottomPage > span.p-skip > input")))
        submit = wait.until(EC.element_to_be_clickable((By.XPATH, '''//*[@id="J_bottomPage"]/span[2]/a''')))
        # 将原本数据清空并赋值
        input.clear()
        input.send_keys(page_number)
        submit.click()
        get_product()
    except Exception:
        next_page(page_number)

def get_product():
    # 等待宝贝信息加载完毕
    wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "#J_goodsList .gl-warp .gl-item .gl-i-wrap")))
    # 获取网页源码
    html = driver.page_source
    doc = pq(html)
    items = doc("#J_goodsList .gl-warp .gl-item .gl-i-wrap").items()
    for item in items:
        # 找到包裹图片的div，用正则取 方法好傻，心碎！！！！！
        item = str(item)
        pattern = re.compile('<div xmlns[\s\S]*?<img width[\s\S]*?src="([\s\S]*?)"/>[\s\S]*?<em>([\s\S]*?)</em>[\s\S]*?<i>([\s\S]*?)</i>[\s\S]*?<div class="p-name p-name-type-2">[\s\S]*?<em>([\s\S]*?)<font class="skcolor_ljg">([\s\S]*?)</font>([\s\S]*?)</em>[\s\S]*?<span class="J_im_icon">[\s\S]*?title="([\s\S]*?)"')
        results = re.findall(pattern, item)
        if len(results) != 0:
            for result in results:
                item = {
                    'image': result[0],
                    'price': result[1]+result[2],
                    'deal': result[3]+result[4]+result[5],
                    'business': result[6]
                }
                print(item)
                save_to_mongo(item)


# 存储到数据库
def save_to_mongo(result):
    try:
        if db[MONGODB_TABLE].insert(result):
            print("存储成功", result)
    except Exception:
        print("存储失败", result)


def main():
    total = int(search())
    for i in range(2, total+1):
        next_page(i)


if __name__ == "__main__":
    main()
