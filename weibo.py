#coding:utf-8

#import selenium
#print selenium.__file__  #打印出导入的路径

from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait #等待时间
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys #键盘
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support import expected_conditions as EC # available since 2.26.0
import time
import os
import json
import ssl
import requests

from pymongo import MongoClient #mongoDB API包


weibo_username=""
weibo_password=""
weibo_stratKey=""

#调试信息
_DEBUG=False 


class UserInfo(object):
    pass


#下载头像
def download_user_headImage(username,url):
    name = 'userImage/%s.jpg' % username
    imageUrl = url
    r = myRequests.get(url=imageUrl,headers=headers)
    imageContent = (r.content)
    fileImage = open(name,'wb')
    fileImage.write(imageContent)
    fileImage.close()
    print('正在下载第：'+username +' 的头像')

#递归搜索好友
def fans_search_user_recursion_function(user,dr):
    global Grade

    for friend in user.friends:
        isFind=db.userInfo.find({"weiboName":friend['name']})#去除重复的
        if isFind.count() != 0:
            continue 

        if friend["name"] == weibo_stratKey :
            continue

        if friend["name"] == "就取一个没有被占用的名字好了":
            continue

        print("\n\n搜索用户:%s 基于^^^%s^^^好友第^^^%d^^^层!" % (friend['name'],weibo_stratKey,4-Grade))
        time.sleep(2)
        dr.find_element_by_css_selector("a[data-type=\'user\']").click()

        print('输入内容：'+friend['name'])
        dr.find_element_by_css_selector("input[name=\"queryVal\"]").click()
        dr.find_element_by_css_selector("input[name=\"queryVal\"]").send_keys(friend['name'])
        dr.find_element_by_class_name("btn-txt").click()

        print("点击头像")
        dr.find_element_by_css_selector("img[data-node=\"cImgUsr\"]").click()
        time.sleep(2)

        #获取用户信息
        user_fans=get_user_info_on_homePage(dr)
        user_fans.index_id=index_id
        user_fans.grade=Grade
        user_fans.gradeName=GradeName

        #存储到数据库
        log=db.userInfo.save(user_fans.__dict__)
        print("mango log:"+str(log))

        print(len(user_fans.followersArray))
        print(len(user_fans.fansArray))

        #返回搜索界面
        dr.find_element_by_css_selector("a.iconf_navbar_back").click()

    return

#下拉刷新
def puss_of_down(elemrnt):
    x=0
    while x<100:
        elemrnt.send_keys(Keys.DOWN) 
        x=x+1

    time.sleep(5)
    return



#到主页获取微博个人信息
def get_user_info_on_homePage(driver_web):
    user=UserInfo()

    #获取头像地址 get_attribute('type')
    user.minHeadImageUrl = driver_web.find_element_by_class_name("mc-main").find_element_by_css_selector('img').get_attribute('src')
    user.maxHeadImageUrl = driver_web.find_element_by_class_name("mc-main").find_element_by_css_selector('img').get_attribute('data-srchd')
    print('大头像:',user.maxHeadImageUrl,'小头像:',user.minHeadImageUrl)

    user.weiboName=driver_web.find_element_by_class_name("mc-main").find_element_by_css_selector("div.item-main").find_element_by_css_selector('span').text
    user.autograph=driver_web.find_element_by_class_name("mc-main").find_element_by_css_selector("div.mct-d").text
    print("名字:",user.weiboName ,"签名:",user.autograph)

    #下载头像
    download_user_headImage(user.weiboName,user.maxHeadImageUrl)

    array=driver_web.find_element_by_css_selector("section.card-combine").find_elements_by_css_selector("a.line-separate")
    user.followers=array[2].find_element_by_css_selector("div.mct-a").text
    user.fans=array[3].find_element_by_css_selector("div.mct-a").text
    print("关注:",user.followers ,"粉丝:",user.fans)

    #详细资料
    driver_web.find_element_by_css_selector("section.card-combine").find_element_by_css_selector("a.box-col").click()
    time.sleep(2)

    DetailDit={}
    Detailall=driver_web.find_element_by_id("profileDetail").find_elements_by_css_selector("div.item-info-page")
    for item in Detailall:
        itemName=item.find_element_by_css_selector('span').text

        itemArray=[]
        for item in item.find_elements_by_css_selector('p'):
             itemArray.append(item.text)

        DetailDit[itemName] = itemArray
    
    print(DetailDit)
    user.DetaiInfo=DetailDit

    #返回主页   
    driver_web.find_element_by_id("gohome").click()
    time.sleep(2)

    #点关注，列表
    driver_web.find_element_by_css_selector("section.card-combine").find_elements_by_css_selector("a.line-separate")[2].find_element_by_css_selector("div.mct-a").click()


    try:
        driver_web.find_element_by_css_selector("div.card-list")
        isLoad=True
    except:
        isLoad=False

    #等待刷线
    while isLoad == False:
        time.sleep(5)
        webdriver.refresh()
        try:
            driver_web.find_element_by_css_selector("div.card-list")
            isLoad=True
        except:
            isLoad=False


    #下拉到最底部
    folarray=driver_web.find_element_by_css_selector("div.card-list").find_elements_by_css_selector("div.line-around")
    x=0
    y=len(folarray)
    while x<y and y<300:
        puss_of_down(driver_web.find_element_by_css_selector("body"))
        x=y
        y=len(driver_web.find_element_by_css_selector("div.card-list").find_elements_by_css_selector("div.line-around"))


    #全部列表
    folarray=driver_web.find_element_by_css_selector("div.card-list").find_elements_by_css_selector("div.line-around")
    followersArray=[]
    for item in folarray:
        follower={}
        follower["imge"]=item.find_element_by_css_selector("img").get_attribute('src')

        index=0
        listTitle=["name","oneWeibo","time","unknowe"]
        for info in item.find_elements_by_css_selector("div.txt-cut"):
            follower[listTitle[index]]=info.text
            index=index+1

        followersArray.append(follower)

    user.followersArray=followersArray
    print("followers：%d" % len(followersArray))

    #返回
    driver_web.find_element_by_css_selector("a.iconf_navbar_back").click()
    time.sleep(1)
    
    #点粉丝 列表
    driver_web.find_element_by_css_selector("section.card-combine").find_elements_by_css_selector("a.line-separate")[3].find_element_by_css_selector("div.mct-a").click()
    time.sleep(2)


    try:
        driver_web.find_element_by_css_selector("div.card-list")
        isLoad=True
    except:
        isLoad=False

    #等待刷线
    while isLoad == False:
        time.sleep(5)
        webdriver.refresh()
        try:
            driver_web.find_element_by_css_selector("div.card-list")
            isLoad=True
        except:
            isLoad=False


    #下拉到最底部
    folarray=driver_web.find_element_by_css_selector("div.card-list").find_elements_by_css_selector("div.line-around")
    x=0
    y=len(folarray)
    while x<y and y<200:
        puss_of_down(driver_web.find_element_by_css_selector("body"))
        x=y
        y=len(driver_web.find_element_by_css_selector("div.card-list").find_elements_by_css_selector("div.line-around"))


    #全部列表
    fanarray=driver_web.find_element_by_css_selector("div.card-list").find_elements_by_css_selector("div.line-around")
    fansArray=[]
    for item in fanarray:
        fans={}
        fans["imge"]=item.find_element_by_css_selector("img").get_attribute('src')

        index=0
        listTitle=["name","oneWeibo","time","unknowe"]
        for info in item.find_elements_by_css_selector("div.txt-cut"):
            fans[listTitle[index]]=info.text
            index=index+1

        fansArray.append(fans)

    user.fansArray=fansArray
    print("fans:%d" % len(fansArray))

    #返回
    driver_web.find_element_by_css_selector("a.iconf_navbar_back").click()
    time.sleep(1)


    #退出主页，返回
    driver_web.find_element_by_css_selector("a.iconf_navbar_back").click()
    time.sleep(2)

    #粉丝数小于300的普通人
    friends=[]
    if len(fansArray) < 200:
        for fan in fansArray:
            for fol in followersArray:
                if fan["name"]==fol["name"]:
                    friends.append(fan)
                    print("friends: "+fan["name"])
    
    user.friends=friends
    print("friends count: %d" % len(user.friends))
    return user

#初始化
def init_webdrive_and_weibo():
    print('打开网站')

    mobile_emulation = {
        "deviceMetrics": { "width": 375, "height": 667, "pixelRatio": 3.0 },
        "userAgent": "Mozilla/5.0 (Linux; Android 4.2.1; en-us; Nexus 5 Build/JOP40D) AppleWebKit/535.19 (KHTML, like Gecko) Chrome/18.0.1025.166 Mobile Safari/535.19" }
    chrome_options = Options()
    chrome_options.add_experimental_option("mobileEmulation", mobile_emulation)
    dr = webdriver.Chrome(chrome_options=chrome_options) 
    dr.maximize_window()
    dr.get("http://www.weibo.com/")

    print("登陆按钮")
    btnLogin=WebDriverWait(dr,10).until(lambda dr :dr.find_element_by_class_name("btnWhite"))
    btnLogin.click()

    print("登陆")
    time.sleep(2)
    name=WebDriverWait(dr,10).until(lambda dr :dr.find_element_by_id("loginName"))
    dr.find_element_by_id("loginName").clear()#清空默认内容
    dr.find_element_by_id("loginName").send_keys(weibo_username)
    dr.find_element_by_id("loginPassword").clear()
    dr.find_element_by_id("loginPassword").send_keys(weibo_password)

    #点击登陆按钮
    dr.find_element_by_id("loginAction").click()
    time.sleep(15)

    return dr


#按深度 搜索好友的好友
def get_user_of_gread(dr):
    global Grade
    global GradeName

    while Grade > 0:
        users=db.userInfo.find({"grade":Grade,"gradeName":GradeName})
        print("grade=%d" % Grade)
        Grade=Grade-1

        for item in users:
            user=UserInfo()
            user.friends= item["friends"]
            print("搜索:**%s**的好友" % item["weiboName"])

            fans_search_user_recursion_function(user,dr)

    return



def main():


    #初始化 下载图片请求
    global myRequests
    global headers
    
    if hasattr(ssl, '_create_unverified_context'):
        ssl._create_default_https_context = ssl._create_unverified_context

    headers = {'User-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_2) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/44.0.2403.125 Safari/537.36'}
    myRequests = requests.Session()
    myRequests.headers.update(headers)
    #初始化mongoDB 数据库
    global db
    client=MongoClient('127.0.0.1',27017)
    db=client['weiboDB']
    collection_useraction = db['userInfo']

    global Grade, GradeName, index_id
    Grade=4
    GradeName=weibo_stratKey
    index_id=1

    dr=init_webdrive_and_weibo()
    print("搜索界面")
    btnSearch=WebDriverWait(dr,30).until(lambda dr :dr.find_element_by_css_selector("a[data-node=\"search\"]"))
    btnSearch.click()


    isFind=db.userInfo.find({"weiboName":weibo_stratKey})#去除重复的
    if isFind.count() != 0:
        time.sleep(1)
        get_user_of_gread(dr)
    else:
        print("用户")
        time.sleep(2)
        dr.find_element_by_css_selector("a[data-type=\'user\']").click()

        print('输入')
        dr.find_element_by_css_selector("input[name=\"queryVal\"]").click()
        dr.find_element_by_css_selector("input[name=\"queryVal\"]").send_keys(weibo_stratKey)
        dr.find_element_by_class_name("btn-txt").click()

        print("点击头像")
        dr.find_element_by_css_selector("img[data-node=\"cImgUsr\"]").click()
        time.sleep(2)

        #获取用户信息
        user=get_user_info_on_homePage(dr)
        user.index_id=index_id
        user.grade=Grade
        user.gradeName=GradeName

        #存储到数据库
        log=db.userInfo.save(user.__dict__)
        print("maogoDB log:"+str(log))
    
        #返回搜索界面
        time.sleep(1)
        dr.find_element_by_css_selector("a.iconf_navbar_back").click()
        time.sleep(1)
        #按配置深度来 递归 #迭代下载粉丝信息
        get_user_of_gread(dr)


    print ('Browser is close')
    dr.quit()


if __name__ == '__main__':
    main()
