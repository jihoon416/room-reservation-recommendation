from bs4 import BeautifulSoup
from selenium import webdriver

import re
import time
import datetime

import json
import os
import random

import sys
from PyQt5.QtWidgets import *

chrome_options = webdriver.ChromeOptions()
chrome_options.add_argument("headless")
chrome_options.add_argument("disable_gpu")

# driver = webdriver.Chrome(chrome_options=chrome_options)
driver = webdriver.Edge()
print("Opening Browser...")
driver.implicitly_wait(3)

driver.get("http://student.gs.hs.kr/student/index.do")
assert "경기과학고등학교" in driver.title

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
        return [self.applicant, self.room, self.timetype, self.start, self.end, self.use, self.useby,
                self.students, self.reason, self.teacher, self.time, self.day, self.state]


def get_data(driver, date):
    url = ("http://student.gs.hs.kr/student/"
       "well/goodsUse.do?"
       "date=%s"
       "&site=MAIN&goodsType=SITE" %date)
    driver.get(url)
    bs = BeautifulSoup(driver.page_source, "html.parser")
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
        if float(early)>0:
            tempx.append(float(early))
            tempy.append(state == "승인" and 1 or 0)
    return [tempx, tempy]


def fetch():
    print("Receiving Data...")

    if os.path.isfile("data.json"):     # 전에 프로그램을 사용했던 적이 있어 json 파일이 있는 경우
        with open("data.json", "r") as f:
            data = json.load(f)
        yesterday = datetime.datetime.now() - datetime.timedelta(1)
        if data["date"] != yesterday.strftime("%Y%m%d"):    # 전 날까지의 정보가 저장되어 있으면 다음 과정을 건너뜀
            datadate = datetime.datetime.strptime(data["date"], "%Y%m%d")
            date_range = [datadate + datetime.timedelta(days=x + 1) for x in range(0, (yesterday - datadate).days)]
            i = 0
            for date in date_range:
                web_data = get_data(driver, date.strftime("%Y%m%d"))
                # print(date.strftime("%Y%m%d"))
                for room in web_data:
                    room_name = room.get_info()[1]
                    if room_name not in data:
                        data[room_name] = [room.get_info()]
                    else:
                        data[room_name].append(room.get_info())
                data["date"] = date.strftime("%Y%m%d")

                i += 1
                if i % 7 == 0:
                    with open("data.json", "w") as f:
                        json.dump(data, f)
    else:   # 처음 json 파일을 만드는 경우
        start = datetime.datetime.strptime("20180302", "%Y%m%d")
        yesterday = datetime.datetime.now() - datetime.timedelta(1)
        date_range = [start + datetime.timedelta(days=x) for x in range(0, (yesterday - start).days + 1)]
        data = dict(date="")
        i = 0
        for date in date_range:
            web_data = get_data(driver, date.strftime("%Y%m%d"))
            # print(date.strftime("%Y%m%d"))
            for room in web_data:
                room_name = room.get_info()[1]
                if room_name not in data:
                    data[room_name] = [room.get_info()]
                else:
                    data[room_name].append(room.get_info())
            data["date"] = date.strftime("%Y%m%d")

            i += 1
            if i % 7 == 0:
                with open("data.json", "w") as f:
                    json.dump(data, f)

    with open("data.json", "w") as f:
        json.dump(data, f)
    print("Collected All Previous Data")
    return data


def get_results(identification, password, num, datee, start, end, data):
    data.pop("date", None)
    # print(data["본관 : 2-7반 [404호]"])
    score = dict()
    room_list = []
    daten = datee.date()
    daten = daten.toPyDate()
    message = ""
    now = datetime.datetime.now()
    use = start.time()
    use = use.toString("HH:mm")
    use = datetime.datetime.strptime(use, "%H:%M").time()
    use = datetime.datetime.combine(daten, use)
    early = (use - now).total_seconds() // 60   # 몇 분 일찍 신청하는지
    for room in data.keys():
        room_list.append(room)
        dataset = ready_data(data, room)
        numerator = [0, 0, 0]
        denominator = [0, 0, 0]
        for i in range(len(dataset[0])):
            t = dataset[0][i]
            state = dataset[1][i]
            if t<60:
                denominator[0] += 1
                if state == 1:
                    numerator[0] += 1
            elif t<150:
                denominator[1] += 1
                if state == 1:
                    numerator[1] += 1
            else:
                denominator[2] += 1
                if state == 1:
                    numerator[2] += 1
        if early<60:    # 1시간 전이 넘어서야 신청할 때
            i = 0
            message = "어쩔 수 없이 늦게 신청하는 것이시겠지만 선생님께 실례를 하는 것임을 명심해주세요!"
        elif early<150:     # 1차시 신청을 기준으로 종례 이후에 신청할 때
            i = 1
            message = "이제야 시간이 나서 신청하는 것이겠지만 되도록이면 종례 전에 신청해주세요!"
        else:
            i = 2
            message = "일찍일찍 신청하는 모습 보기 좋아요!"
        if denominator[i] == 0:
            if numerator[i] == 0:
                score[room] = 0
            else:
                score[room] = 0
        else:
            score[room] = numerator[i]/denominator[i]
    web_data = get_data(driver, daten.strftime("%Y%m%d"))
    print("Sorted All Data")
    for room in web_data:
        room_name = room.get_info()[1]
        # print(room_name)
        timestart = datetime.datetime.strptime(room.get_info()[3], "%Y%m%d%H%M")
        timeend = datetime.datetime.strptime(room.get_info()[4], "%Y%m%d%H%M")
        s = start.time()
        s = s.toString("HH:mm")
        s = datetime.datetime.strptime(s, "%H:%M").time()
        s = datetime.datetime.combine(daten, s)
        e = end.time()
        e = e.toString("HH:mm")
        e = datetime.datetime.strptime(e, "%H:%M").time()
        e = datetime.datetime.combine(daten, e)
        # print(timestart)
        # print(s)
        if (timestart<e and timeend>s) or (timestart>e and timeend<s):  # 사용하고자 하는 시간대가 이미 신청한 곳과 겹치는 경우
            if room_name in room_list:
                room_list.remove(room_name)
            score.pop(room_name, None)
    room_list.remove("본관 : 강당 [강당]")
    score.pop("본관 : 강당 [강당]")
    output = []
    for room in score.keys():
        output.append(room)     # 사용 가능한 방 list에 추가
        # print(room, end=" : ")
        # print(score[room])
    i = 0
    recom = []
    avg = 0
    n = 0
    for room in sorted(score, key=score.get, reverse=True):     # 확률에 대한 내림차순으로 배열
        i += 1
        recom.append(room)      # 추천 방 list에 추가
        avg += score[room]
        n += 1
        if i==3:    # 3개까지만 출력
            break
    avg = avg/n
    message += "\n"+"승인 평균 확률: "+str(round(avg,2)*100)+"%\n"
    if early < 60:
        if avg*100<50:      # 만약 평균 확률이 50%가 안 되는 경우
            message += "아쉽지만 이미 신청이 많이 늦은 것 같습니다..."
    elif early < 150:
        if avg*100<50:      # 만약 평균 확률이 50%가 안 되는 경우
            message += "다음에는 조금만 더 일찍하면 승인이 더 잘 될 수 있을 것입니다!"

    # print("Hello World!")

    return [output, recom, message]


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setGeometry(600, 300, 500, 400)
        self.setWindowTitle("The Room")

        self.id = None
        self.pw = None

        login = LoginDialog()
        login.exec_()
        self.id = login.id
        self.pw = login.password

        id = driver.find_element_by_name("tempUserId")
        id.clear()
        id.send_keys(self.id)
        pw = driver.find_element_by_name("tempPwd")
        pw.clear()
        pw.send_keys(self.pw)
        driver.find_element_by_css_selector("#user > div.row > div.col-xs-4 > button").click()      # 송죽학사 로그인 페이지에 로그인

        time.sleep(3)
        data = fetch()

        widget = Widgets()
        widget.exec_()
        self.num = widget.num
        self.date = widget.date
        self.timeStart = widget.timeStart
        self.timeEnd = widget.timeEnd

        text = TextDialog(self.id, self.pw, self.num, self.date, self.timeStart, self.timeEnd, data)
        self.setCentralWidget(text)
        self.close()


class LoginDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.initUI()
        self.id = None
        self.password = None

    def initUI(self):
        self.setGeometry(500, 300, 300, 100)
        self.setWindowTitle("송죽학사 로그인")

        labelid = QLabel("ID")
        labelpw = QLabel("Password")

        self.lineEditID = QLineEdit()
        self.lineEditPW = QLineEdit()
        self.lineEditPW.setEchoMode(QLineEdit.Password)
        self.btn = QPushButton("Login")
        self.btn.clicked.connect(self.btnClicked)

        layout = QGridLayout()
        layout.addWidget(labelid, 0, 0)
        layout.addWidget(self.lineEditID, 0, 1)
        layout.addWidget(labelpw,1,0)
        layout.addWidget(self.lineEditPW, 1, 1)
        layout.addWidget(self.btn, 2, 1)

        self.setLayout(layout)

    def btnClicked(self):
        self.id = self.lineEditID.text()
        self.password = self.lineEditPW.text()
        self.close()


class Widgets(QDialog):
    def __init__(self):
        super().__init__()

        self.setGeometry(100, 300, 400, 300)
        self.setWindowTitle("Input Window")
        self.num = 0
        self.done = False

        label_num = QLabel("신청 학생 수", self)
        label_date = QLabel("날짜", self)
        label_start = QLabel("시작 일시", self)
        label_end = QLabel("종료 일시", self)

        self.lineEditNum = QLineEdit()

        self.date = QDateEdit()
        self.date.setMinimumDate(datetime.datetime.today())     # 선택할 수 있는 최소 날짜
        self.date.setMaximumDate(datetime.date(2019, 2, 28))    # 선택할 수 있는 최대 날짜
        self.date.setCalendarPopup(True)    # 달력이 튀어나오도록
        self.calendar = self.date.calendarWidget()

        self.timeStart = QTimeEdit()
        self.timeEnd = QTimeEdit()

        self.btn_run = QPushButton("RUN")
        self.btn_run.clicked.connect(self.run)

        layout = QGridLayout()
        layout.addWidget(label_num, 0, 0)
        layout.addWidget(self.lineEditNum, 0, 1)
        layout.addWidget(label_date, 1, 0)
        layout.addWidget(self.date, 1, 1)
        layout.addWidget(label_start, 2, 0)
        layout.addWidget(self.timeStart, 2, 1)
        layout.addWidget(label_end, 3, 0)
        layout.addWidget(self.timeEnd, 3, 1)
        layout.addWidget(self.btn_run, 4, 1)

        self.setLayout(layout)

    def run(self):
        self.num = self.lineEditNum.text()
        # get_results(self.id, self.pw, self.num, self.date, self.timeStart, self.timeEnd)

        self.done = True
        # print("Hello")
        self.close()


class TextDialog(QWidget):
    def __init__(self, id, pw, num, date, timeStart, timeEnd, data):
        super().__init__()
        self.id = id
        self.pw = pw
        self.num = num
        self.date = date
        self.timeStart = timeStart
        self.timeEnd = timeEnd
        self.data = data
        self.initUI()

    def initUI(self):
        self.setGeometry(600, 300, 500, 700)
        self.setWindowTitle("결과 출력")

        self.results = get_results(self.id, self.pw, self.num, self.date, self.timeStart, self.timeEnd, self.data)
        results = "비어있는 강의실 :\n"
        for room in self.results[0]:
            results += (str(room)+"\n")
        results += "\n\n"
        results += "추천 강의실 :\n"
        recom = self.results[1]
        while recom:
            random.shuffle(recom)   # 윤리적인 문제로 확률 순서는 random으로
            results += (str(recom.pop())+"\n")
        results += "\n"

        results += self.results[2]


        self.outText = QTextEdit()
        self.outText.setReadOnly(True)
        self.outText.setLineWrapMode(QTextEdit.NoWrap)

        self.outText.insertPlainText(results)

        nlayout = QGridLayout()
        nlayout.addWidget(self.outText, 0, 0)

        self.setLayout(nlayout)


if __name__=="__main__":
    try:
        app = QApplication(sys.argv)
        window = MainWindow()
        window.show()
        app.exec_()
    finally:
        print("Closing Browser")
        driver.quit()

# print("Bye World!")