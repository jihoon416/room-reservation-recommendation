import sys
from PyQt5.QtWidgets import *

import datetime

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setGeometry(600, 300, 200, 150)
        self.setWindowTitle("The Room")

        self.id = None
        self.pw = None

        login = LoginDialog()
        login.exec_()
        self.id = login.id
        self.pw = login.password

        widget = Widgets(self.id, self.pw)
        self.setCentralWidget(widget)


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


class Widgets(QWidget):
    def __init__(self, id, pw):
        super().__init__()

        self.setGeometry(100, 300, 200, 150)
        self.setWindowTitle("Widget")

        self.id = id
        self.pw = pw

        label_num = QLabel("신청 학생 수", self)
        label_date = QLabel("날짜", self)
        label_start = QLabel("시작 일시", self)
        label_end = QLabel("종료 일시", self)

        self.lineEditNum = QLineEdit()

        self.date = QDateEdit()
        self.date.setMinimumDate(datetime.datetime.today())
        self.date.setMaximumDate(datetime.date(2019, 2, 28))
        self.date.setCalendarPopup(True)
        self.calendar = self.date.calendarWidget()

        self.timeStart = QTimeEdit()
        self.timeEnd = QTimeEdit()

        self.btn_run = QPushButton("RUN")
        self.btn_run.clicked.connect(self.run)

        self.text = QTextEdit()

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
        layout.addWidget(self.text, 5, 1)

        self.setLayout(layout)

    def run(self):
        self.num = self.lineEditNum.text()
        # get_results(self.id, self.pw, self.num, self.date, self.timeStart, self.timeEnd)
        self.close()


if __name__=="__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    app.exec_()