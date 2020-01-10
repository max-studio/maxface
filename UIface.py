# coding = utf-8
import sys
from PyQt5 import QtWidgets
from PyQt5.QtWidgets import (QApplication, QMenuBar, QGridLayout, QPushButton, QDialog,
                             QLabel, QTableWidget, QHeaderView, QLineEdit, QFormLayout)
from PyQt5.QtGui import QPixmap, QFont
from PyQt5.QtCore import QDate, QTime, QTimer, Qt

from face_dbinit import *

style_file = './UIface.qss'


class MainUI(QtWidgets.QWidget):
    """
    应用主界面
    """
    
    def __init__(self, parent=None):
        """
        页面元素初始化
        :param parent:
        """
        super(MainUI, self).__init__(parent)
        # 窗口属性初始化
        # self.resize(920, 560)
        self.setFixedSize(920, 560)
        self.setWindowTitle("MaX.打卡系统--V1.0")
        
        # 变量初始化
        self.menu_bar = None  # 菜单栏
        self.logcat_menu = None  # 打卡日志
        self.admin_login = None  # 管理员登录
        self.image = None  # 图片初始化
        self.button_in = None  # 输入按钮
        self.button_check = None  # 打卡按钮
        self.widget = None  # 控件
        self.time_label = None  # 时间标签
        self.name_label = None  # 打卡名字显示
        self.time = None  # 获取当前时间
        self.date = None  # 获取当前日期
        self.timer = None  # 定时器
        self.text = None  # 时间格式化
        self.log_dialog = None  # 日志弹窗
        self.admin_dialog = None  # 管理员弹窗
        self.info_dialog = None  # 信息录入弹窗
        
        # 布局初始化
        self.glayout = QGridLayout()
        self.glayout.setSpacing(10)
        self.setLayout(self.glayout)
        
        # 动态显示时间
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.current_time)
        
        self.timer.start()
        # 函数初始化
        self.set_menu()
        self.show_time_label()
        self.current_time()
        self.set_operation()
        self.set_image()
        self.show_name_label()
        self.clicked_activity()
    
    def clicked_activity(self):
        """
        控件信号处理
        :return:
        """
        
        self.logcat_menu.triggered.connect(lambda: self.on_log_dialog())
        self.admin_login.triggered.connect(lambda: self.on_admin_dialog())
        self.button_in.clicked.connect(lambda: self.on_info_dialog())
    
    def set_menu(self):
        """
        菜单栏部分界面
        :return:
        """
        
        self.menu_bar = QMenuBar(self)  # 菜单栏
        self.menu_bar.setObjectName('menu_bar')
        self.logcat_menu = self.menu_bar.addAction("打卡日志")
        self.menu_bar.addSeparator()
        self.admin_login = self.menu_bar.addAction("管理员登录")
        self.glayout.addWidget(self.menu_bar, 0, 0, 1, 30)
    
    def set_operation(self):
        """
        点击按钮
        :return:
        """
        self.button_in = QPushButton("录入人脸")
        self.button_in.setObjectName('button_in')
        self.button_check = QPushButton("开始打卡")
        self.button_check.setObjectName('button_check')
        self.glayout.addWidget(self.button_in, 10, 2, 10, 10)
        self.glayout.addWidget(self.button_check, 12, 2, 10, 10)
    
    def set_image(self):
        """
        预设图片
        :return:
        """
        self.image = QLabel(self)
        self.image.setObjectName('image')
        self.image.setPixmap(QPixmap(r"G:\githublocal\drawable\MaXlogo.jpg").scaled(600, 400))
        self.glayout.addWidget(self.image, 1, 15, 15, 15)
    
    def show_time_label(self):
        """
        打卡时间显示
        :return:
        """
        # widget = QtWidgets.QWidget()
        self.time_label = QLabel()
        self.time_label.setObjectName('time_label')
        self.time_label.setFrameShape(QtWidgets.QFrame.Box)
        self.glayout.addWidget(self.time_label, 3, 0, 8, 15)
    
    def show_name_label(self):
        """
        打卡姓名显示
        :return:
        """
        self.name_label = QLabel(self)
        self.name_label.setObjectName('name_label')
        self.name_label.setText("暂无打卡信息")
        self.name_label.setAlignment(Qt.AlignCenter)
        # self.name_label.setGeometry(50, 500, 20, 20)
        self.name_label.setFrameShape(QtWidgets.QFrame.Box)
        self.glayout.addWidget(self.name_label, 16, 17, 4, 10)
    
    def current_time(self):
        """
        获取当前日期时间，显示到label标签
        :return:
        """
        self.date = QDate.currentDate()
        self.time = QTime.currentTime()
        self.text = self.date.toString(Qt.DefaultLocaleLongDate) + "\n" + self.time.toString()
        self.time_label.setText(self.text)
        self.time_label.setAlignment(Qt.AlignCenter)  # 字体居中
    
    # @staticmethod
    def on_log_dialog(self):
        logcat = LogDialog()
        logcat.setStyleSheet(CommonHelper.read_qss(style_file))
        self.log_dialog = logcat.exec_()
    
    def on_admin_dialog(self):
        admin = AdminDialog()
        admin.setStyleSheet(CommonHelper.read_qss(style_file))
        self.admin_dialog = admin.exec_()
        if admin.contrast():
            self.admin_login.setText(admin.contrast())  # 更改菜单名
    
    def on_info_dialog(self):
        info = InfoDialog()
        info.setStyleSheet(CommonHelper.read_qss(style_file))
        self.info_dialog = info.exec_()


class LogDialog(QDialog):
    """
    日志弹窗类
    """
    
    def __init__(self, parent=None):
        super(LogDialog, self).__init__(parent)
        self.setWindowTitle("打卡日志")
        self.setWindowModality(Qt.ApplicationModal)  # 隐藏父窗口
        self.setFixedSize(500, 480)
        
        self.table = None
        self.button_export = None
        self.log_dialog()
    
    def log_dialog(self):
        """
        日志弹窗
        :return:
        """
        self.table = QTableWidget(500, 5, self)
        self.table.resize(500, 400)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)  # 设置表单不可编辑
        self.table.setSelectionMode(QTableWidget.NoSelection)  # 设置表单不可选中
        header = ["ID", "姓名", "打卡时间", "是否迟到", "迟到时长"]
        self.table.setHorizontalHeaderLabels(header)
        self.table.resizeColumnsToContents()  # 列根据内容调整大小
        self.table.resizeRowsToContents()  # 行根据内容调整大小
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)  # 表单自适应
        
        self.button_export = QPushButton("导出日志", self)
        self.button_export.move(180, 415)


class AdminDialog(QDialog):
    """
    管理员登录弹窗
    """
    
    def __init__(self, parent=None):
        super(AdminDialog, self).__init__(parent)
        self.setFixedSize(350, 250)
        self.setWindowTitle("管理员登录")
        self.setWindowModality(Qt.ApplicationModal)
        self.setAutoFillBackground(True)
        self.label_name = None
        self.label_passwd = None
        self.button_login = None
        self.name_edit = None
        self.passwd_edit = None
        self.glayout = None
        self.admin_name = None
        
        self.set_login()
        self.admin_layout()
        self.activity()
    
    def activity(self):
        self.button_login.clicked.connect(lambda: self.contrast())
    
    def set_login(self):
        self.label_name = QLabel("用户名:", self)
        self.label_name.setFont(QFont("Roman times", 15, QFont.Bold))
        self.label_name.setAlignment(Qt.AlignCenter)
        self.label_passwd = QLabel("密码:", self)
        self.label_passwd.setFont(QFont("Roman times", 15, QFont.Bold))
        self.label_passwd.setAlignment(Qt.AlignCenter)
        self.name_edit = QLineEdit(self)
        self.name_edit.setFont(QFont("Roman times", 15, QFont.Bold))
        self.passwd_edit = QLineEdit(self)
        self.passwd_edit.setFont(QFont("Roman times", 15, QFont.Bold))
        self.passwd_edit.setEchoMode(QLineEdit.Password)
        self.button_login = QPushButton("登录")
    
    def admin_layout(self):
        self.glayout = QGridLayout(self)
        self.glayout.addWidget(self.label_name, 0, 0)
        self.glayout.addWidget(self.label_passwd, 1, 0)
        self.glayout.addWidget(self.name_edit, 0, 1, 1, 2)
        self.glayout.addWidget(self.passwd_edit, 1, 1, 1, 2)
        self.glayout.addWidget(self.button_login, 2, 1)
    
    def contrast(self):
        """
        将用户名、密码与数据库进行对比
        :return:
        """
        self.admin_name = load_admin(self.name_edit.text(), self.passwd_edit.text())
        if self.admin_name:
            self.close()
            return self.admin_name
        else:
            pass


class InfoDialog(QDialog):
    """
    录入信息填写
    """
    
    def __init__(self, parent=None):
        super(InfoDialog, self).__init__(parent)
        self.setFixedSize(350, 200)
        self.setWindowTitle("信息")
        self.setWindowModality(Qt.ApplicationModal)
        
        self.flayout = None
        self.id_edit = None
        self.name_edit = None
        self.department_edit = None
        self.button_next = None
        
        self.set_info()
    
    def set_info(self):
        self.flayout = QFormLayout()
        id_label = QLabel("ID:")
        id_label.setFont(QFont("Roman times", 15, QFont.Bold))
        id_label.setAlignment(Qt.AlignCenter)
        name_label = QLabel("姓名:")
        name_label.setFont(QFont("Roman times", 15, QFont.Bold))
        name_label.setAlignment(Qt.AlignCenter)
        department_label = QLabel("部门:")
        department_label.setFont(QFont("Roman times", 15, QFont.Bold))
        department_label.setAlignment(Qt.AlignCenter)
        self.id_edit = QLineEdit()
        self.id_edit.setFont(QFont("Roman times", 15, QFont.Bold))
        self.name_edit = QLineEdit()
        self.name_edit.setFont(QFont("Roman times", 15, QFont.Bold))
        self.department_edit = QLineEdit()
        self.department_edit.setFont(QFont("Roman times", 15, QFont.Bold))
        self.button_next = QPushButton("下一步")
        
        self.flayout.addRow(id_label, self.id_edit)
        self.flayout.addRow(name_label, self.name_edit)
        self.flayout.addRow(department_label, self.department_edit)
        self.flayout.addWidget(self.button_next)
        self.setLayout(self.flayout)


class CommonHelper:
    def __init__(self):
        pass
    
    @staticmethod
    def read_qss(stylefile):
        with open(stylefile, 'r') as f:
            return f.read()


if __name__ == '__main__':
    App = QApplication(sys.argv)
    style = CommonHelper.read_qss(style_file)
    ex = MainUI()
    ex.setStyleSheet(style)
    ex.show()
    sys.exit(App.exec_())
