from bs4 import BeautifulSoup
from selenium import webdriver

import re

import datetime
import time

import pickle
import os

import numpy as np
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.neighbors import KNeighborsClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.svm import LinearSVC, SVC
from sklearn.gaussian_process import GaussianProcessClassifier
from sklearn.gaussian_process.kernels import RBF
from sklearn.tree import DecisionTreeClassifier
from sklearn.ensemble import RandomForestClassifier, AdaBoostClassifier
from sklearn.naive_bayes import GaussianNB
from sklearn.discriminant_analysis import QuadraticDiscriminantAnalysis
from sklearn.neural_network import MLPClassifier

import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap


class Room:
    def __init__(self, data, day, permit):   # 혹시 모르니까 있는 정보를 다 저장
        self.applicant = data[0]    # 신청자
        self.room = data[1]     # 사용신청
        self.timetype = data[2]     # 시간구분
        self.start = data[3]    # 시작일시
        self.end = data[4]      # 종료일시
        self.use = data[5]      # 사용구분
        self.useby = data[6]    # 사용대상
        self.students = data[7]     # 사용학생 (list로 저장)
        self.reason = data[8]   # 사유
        self.teacher = data[9]  # 관리교사
        self.time = data[10]    # 신청시간
        self.day = day      # 요일
        self.state = permit     # 승인 여부

    def get_info(self):
        return [self.applicant, self.room, self.timetype, self.start, self.end, self.use, self.useby, self.students, self.reason, self.teacher, self.time, self.day, self.state]


def get_data(date):
    url = ("http://student.gs.hs.kr/student/"
       "well/goodsUse.do?"
       "date=%s"
       "&site=MAIN&goodsType=SITE" %date)
    driver.get(url)
    bs = BeautifulSoup(driver.page_source, "html.parser")

    '''
    day = bs.select("#titleDate > span")[0].text
    day = day.replace("[", "")
    day = day.replace("]", "")
    day = day.replace("년", "")
    day = day.replace("월", "")
    day = day.replace("일", "")
    day = day.replace(" ", "")
    day = re.sub(r"\d", "", day)
    print(day)
    '''
    date = datetime.datetime.strptime(date, "%Y%m%d")
    day = date.isoweekday()
    # print(day)

    rows = bs.select("#listTable > table > tbody > tr > td.item > span")
    rooms = []
    links = []
    for row in rows:
        row_links = row.find_all("a")
        y = False
        yes_links = []
        for link in row_links:
            if link.find("span")["class"] == ["useTime", "userTimeY"]:  # 한 방에 승인된 것이 있고 미승인된 것이 있으면 잘못 신청된 경우이므로 배제
                yes_links.append(link)
                y = True
        if not y:
            for link in row_links:
                links.append(link)
        else:
            for link in yes_links:
                links.append(link)

    for link in links:
        popurl = "http://student.gs.hs.kr"+link.get("href")
        driver.get(popurl)
        bspop = BeautifulSoup(driver.page_source, "html.parser")
        temp = bspop.select("#student > ul > li > dl > dd")
        loc = 9     # 관련교사 항목이 몇 번째인지 결정 (신청학생들 목록이 없는 경우 때문)
        if not temp[7].find_all("li"):
            temp.insert(7, ["Dummy"]*384)
            loc = 8
        else:
            temp[7] = temp[7].find_all("li")
            for k in range(len(temp[7])):
                temp[7][k] = str(temp[7][k])
                temp[7][k] = temp[7][k].replace("<li>", "")
                temp[7][k] = temp[7][k].replace("</li>", "")
                temp[7][k] = temp[7][k].replace("\n", "")
                temp[7][k] = re.sub(r"\s\s+", "", temp[7][k])
        if bspop.select("#student > ul > li > dl > dt")[loc].text == "관련교사":  # 관련교사 항목은 삭제해야 데이터가 동일
            del temp[9]
        for i in [0,1,2,5,9]:
            temp[i] = temp[i].text
            temp[i] = temp[i].replace("\n", "")
            temp[i] = re.sub(r"\s\s+", "", temp[i])
        for i in [3,4,10]:
            temp[i] = temp[i].find("span")["title"]
        for i in [6,8]:
            temp[i] = temp[i].find("xmp")
            temp[i] = str(temp[i])
            temp[i] = temp[i].replace("<xmp>", "")
            temp[i] = temp[i].replace("</xmp>", "")
        state = bspop.select("#hrText")[0].text
        state = state.replace("\n", "")
        state = re.sub(r"\s\s+", "", state)
        # print(popurl+" : "+state)
        rooms.append(Room(temp, day, state))
    return rooms


def ready_data(data, room_name):
    a = data[room_name]
    tempx = []
    tempy = []
    for app in a:
        start_time = datetime.datetime.strptime(app[3], "%Y%m%d%H%M")     # 사용 시작 시간
        app_time = datetime.datetime.strptime(app[10], "%Y-%m-%d %H:%M:%S.%f")  # 신청 시간
        early = (start_time-app_time).total_seconds()//60   # 몇 분 전에 신청했는지
        num_students = len(app[7])  # 신청 인원 수
        if num_students == 384:
            continue
        day = app[11]
        state = app[12]     # 승인 여부
        tempx.append([float(early), float(num_students)])
        tempy.append(state == "승인" and 1 or 0)
    data_x = np.asarray(tempx)
    data_y = np.asarray(tempy)
    data_x_train, data_x_test, data_y_train, data_y_test = train_test_split(data_x, data_y, test_size=0.25, random_state=40)
    scaler = StandardScaler()
    scaler.fit(data_x_train)
    return [data_x_train, data_y_train, data_x_test, data_y_test, scaler]


# get_data("20180607")
if os.path.isfile("data.pickle"):
    pickle_load = open("data.pickle", "rb")
    data = pickle.load(pickle_load)
    yesterday = datetime.datetime.now() - datetime.timedelta(1)
    if data["date"] != yesterday.strftime("%Y%m%d"):
        chrome_options = webdriver.ChromeOptions()
        chrome_options.add_argument("headless")
        chrome_options.add_argument("disable_gpu")

        # driver = webdriver.Chrome(chrome_options=chrome_options)
        driver = webdriver.Edge()
        driver.implicitly_wait(3)

        driver.get("http://student.gs.hs.kr/student/index.do")
        assert "경기과학고등학교" in driver.title

        id = driver.find_element_by_name("tempUserId")
        id.clear()
        id.send_keys("16046")
        pw = driver.find_element_by_name("tempPwd")
        pw.clear()
        pw.send_keys("@atReality319")
        driver.find_element_by_css_selector("#user > div.row > div.col-xs-4 > button").click()
        time.sleep(5)

        datadate = datetime.datetime.strptime(data["date"], "%Y%m%d")
        date_range = [datadate + datetime.timedelta(days=x+1) for x in range(0, (yesterday - datadate).days-1)]
        data["date"] = yesterday.strftime("%Y%m%d")
        for date in date_range:
            web_data = get_data(date.strftime("%Y%m%d"))
            # print(date.strftime("%Y%m%d"))
            for room in web_data:
                room_name = room.get_info()[1]
                if room_name not in data:
                    data[room_name] = [room.get_info()]
                else:
                    data[room_name].append(room.get_info())

        pickle_save = open("data.pickle", "wb")
        pickle.dump(data, pickle_save)
        pickle_save.close()

        driver.quit()
else:
    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument("headless")
    chrome_options.add_argument("disable_gpu")

    # driver = webdriver.Chrome(chrome_options=chrome_options)
    driver = webdriver.Edge()
    driver.implicitly_wait(3)

    driver.get("http://student.gs.hs.kr/student/index.do")
    assert "경기과학고등학교" in driver.title

    id = driver.find_element_by_name("tempUserId")
    id.clear()
    id.send_keys("16046")
    pw = driver.find_element_by_name("tempPwd")
    pw.clear()
    pw.send_keys("@atReality319")
    driver.find_element_by_css_selector("#user > div.row > div.col-xs-4 > button").click()
    time.sleep(5)

    start = datetime.datetime.strptime("20180302", "%Y%m%d")
    yesterday = datetime.datetime.now() - datetime.timedelta(1)
    date_range = [start + datetime.timedelta(days=x) for x in range(0, (yesterday-start).days)]
    data = dict(date=yesterday.strftime("%Y%m%d"))
    for date in date_range:
        web_data = get_data(date.strftime("%Y%m%d"))
        # print(date.strftime("%Y%m%d"))
        for room in web_data:
            room_name = room.get_info()[1]
            if room_name not in data:
                data[room_name] = [room.get_info()]
            else:
                data[room_name].append(room.get_info())

    # print(data["본관 : 2-8반 [405호]"])

    pickle_save = open("data.pickle", "wb")
    pickle.dump(data, pickle_save)
    pickle_save.close()

    driver.quit()

data.pop("date", None)
for room in data.keys():
# for room in ["본관 : 2-2반 [302호]"]:
    dataset = ready_data(data, room)
    scaler = dataset[4]
    data_x_train = scaler.transform(dataset[0])
    data_y_train = dataset[1]
    data_x_test = scaler.transform(dataset[2])
    data_y_test = dataset[3]
    '''
    for k in range(len(data_x_train)):
        print(str(dataset[0][k])+" : "+str(dataset[1][k]))
    for k in range(len(data_x_test)):
        print(str(dataset[2][k])+" : "+str(dataset[3][k]))
    '''
    # classifier = KNeighborsClassifier(3)
    # classifier = LogisticRegression()
    # classifier = SVC(gamma=2, C=1, probability=True)
    # classifier = SVC(kernel="linear", C=0.025, probability=True)
    # classifier = GaussianProcessClassifier(1.0 * RBF(1.0))
    # classifier = DecisionTreeClassifier(max_depth=5)
    # classifier = RandomForestClassifier(max_depth=5, n_estimators=10, max_features=1)
    classifier = MLPClassifier(alpha=1)
    # classifier = AdaBoostClassifier()
    # classifier = GaussianNB()
    # classifier = QuadraticDiscriminantAnalysis()

    classifier.fit(data_x_train, data_y_train)
    # print(data_y_train)
    # print(classifier.predict(data_x_test))
    # print(classifier.predict_proba(data_x_test))
    # print(data_y_test)
    print(room+" : "+str(classifier.score(data_x_test, data_y_test)))

    X = np.append(data_x_train, data_x_test,axis=0)
    h = 0.02
    x_min, x_max = X[:, 0].min() - 0.5, X[:, 0].max() + 0.5
    y_min, y_max = X[:, 1].min() - 0.5, X[:, 1].max() + 0.5
    xx, yy = np.meshgrid(np.arange(x_min, x_max, h), np.arange(y_min, y_max, h))
    if hasattr(classifier, "decision_function"):
        Z = classifier.decision_function(np.c_[xx.ravel(), yy.ravel()])
    else:
        Z = classifier.predict_proba(np.c_[xx.ravel(), yy.ravel()])[:, 1]
    Z = Z.reshape(xx.shape)
    plt.contourf(xx, yy, Z, cmap=plt.cm.RdBu, alpha=0.8)

    cm = ListedColormap(['#FF0000', '#0000FF'])
    plt.scatter(data_x_train[:, 0], data_x_train[:, 1], c=data_y_train, cmap=cm, edgecolors="k")
    plt.scatter(data_x_test[:, 0], data_x_test[:, 1], c=data_y_test, cmap=cm, edgecolors="k", alpha=0.6)
    # plt.show()

'''
for room in data.keys():
    print(room+" : "+str(len(data[room])))
'''

print("Hello World!")

#listTable > table > tbody > tr > td.item > span > a
#hrText
#student > ul > li:nth-child(2) > dl > dd
#student > ul > li:nth-child(2) > dl > dt
#student > ul > li:nth-child(1) > dl > dd
#student > ul > li:nth-child(6) > dl > dd
#student > ul > li:nth-child(8) > dl > dd > ul > li:nth-child(1)
#student > ul > li:nth-child(7) > dl > dd > div.preWrap > xmp