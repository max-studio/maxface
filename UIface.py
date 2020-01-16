# coding = utf-8
import sys
import os
from PyQt5 import QtWidgets
from PyQt5.QtWidgets import (QApplication, QMenuBar, QGridLayout, QPushButton, QDialog,
                             QLabel, QTableView, QHeaderView, QLineEdit, QFormLayout, QMessageBox)
from PyQt5.QtGui import QPixmap, QFont, QImage
from PyQt5.QtCore import QDate, QTime, QTimer, Qt
from PyQt5.QtSql import QSqlDatabase, QSqlQueryModel
from PyQt5.Qt import QThread, QMutex
from skimage import io as io2
from face_dbinit import *
import numpy as np
import cv2
import dlib

style_file = './UIface.qss'
facerec = dlib.face_recognition_model_v1("./model/dlib_face_recognition_resnet_model_v1.dat")
# Dlib 预测器
detector = dlib.get_frontal_face_detector()
predictor = dlib.shape_predictor('./model/shape_predictor_68_face_landmarks.dat')
Path_face = "./data/face_img_database/"


def distance(face_1, face_2):
    """
    计算欧式距离
    :param face_1:
    :param face_2:
    :return:
    """
    face_1 = np.array(face_1)
    face_2 = np.array(face_2)
    dist = np.sqrt(np.sum(np.square(face_1 - face_2)))
    if dist > 0.4:
        return False
    else:
        return True


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
        self.pic_num = 0  # 图片存储标记，最多存储15张人脸
        self.sign = 1  # 标记，1代表打卡，2代表录入
        self.idn = None  # id号
        # 相机定时器
        self.timer_camera = QTimer()
        self.cap = cv2.VideoCapture()  # 设置相机
        
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
        self.button_check.clicked.connect(lambda: self.new_create_time())
        self.timer_camera.timeout.connect(lambda: self.show_camera())
    
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
        idnumber = info.insert_data()
        if idnumber is not None:
            self.idn = idnumber
            self.sign = 2
            self.new_create_time()
    
    def new_create_time(self):
        if self.timer_camera.isActive() is False:
            
            flag = self.cap.open(0)
            if flag is False:
                QMessageBox.warning(self, u"警告", u"请检测相机与电脑是否连接正确",
                                    buttons=QMessageBox.Ok,
                                    defaultButton=QMessageBox.Ok)
            else:
                self.timer_camera.start(30)
                if self.sign == 1:
                    self.feature = load_face()
                    self.button_check.setText("停止打卡")
        else:
            self.timer_camera.stop()
            self.sign = 1
            self.cap.release()
            self.button_check.setText("开始打卡")
            self.name_label.setText("暂无打卡信息")
            self.image.setPixmap(QPixmap(r"G:\githublocal\drawable\MaXlogo.jpg").scaled(600, 400))
    
    def show_camera(self):
        flag, self.im_rd = self.cap.read()
        # key = cv2.waitKey(10)
        # 人脸数
        dets = detector(self.im_rd, 1)
        # 检测到人脸
        if len(dets) != 0:
            equal_face = dets[0]
            # 占比最大的脸
            max_area = 0
            for det in dets:
                w = det.right() - det.left()
                h = det.top() - det.bottom()
                if w * h > max_area:
                    equal_face = det
                    max_area = w * h
                    # 绘制矩形框
            cv2.rectangle(self.im_rd, tuple([equal_face.left(), equal_face.top()]),
                          tuple([equal_face.right(), equal_face.bottom()]),
                          (255, 0, 0), 2)
            show = cv2.resize(self.im_rd, (600, 400))
            show = cv2.cvtColor(show, cv2.COLOR_BGR2RGB)
            show_image = QImage(show.data, show.shape[1], show.shape[0], QImage.Format_RGB888)
            self.image.setPixmap(QPixmap.fromImage(show_image))
            
            if self.sign == 2:
                # 保存截图
                face_height = equal_face.bottom() - equal_face.top()
                face_width = equal_face.right() - equal_face.left()
                im_blank = np.zeros((face_height, face_width, 3), np.uint8)  # 初始化一个三通道的图像矩阵
                # print(im_blank)
                try:
                    
                    for height in range(face_height):
                        for width in range(face_width):
                            im_blank[height][width] = self.im_rd[int(equal_face.top()) + height][
                                int(equal_face.left()) + width]
                    self.pic_num += 1
                    cv2.imwrite(Path_face + self.idn + "/face_img" + str(self.pic_num) + ".jpg",
                                im_blank)  # 中文路径无法存储,故采用id为文件名
                    if self.pic_num >= 15:  # 当提取了15张图后，结束提取
                        into_db = ThreadIntoDB(self.idn)
                        into_db.start()
                        self.pic_num = 0
                        self.new_create_time()
                except:
                    print("异常")
            else:
                try:
                    shape = predictor(self.im_rd, equal_face)
                    face_cap = facerec.compute_face_descriptor(self.im_rd, shape)
                    
                    # 将当前人脸与数据库人脸对比
                    for i, face_data in enumerate(self.feature[1]):
                        compare = distance(face_cap, face_data)
                        if compare is True:
                            self.name_label.setText(str(self.feature[0][i]))
                except:
                    print("异常")


class LogDialog(QDialog):
    """
    日志弹窗类
    """
    
    def __init__(self, parent=None):
        super(LogDialog, self).__init__(parent)
        self.setWindowTitle("打卡日志")
        self.setWindowModality(Qt.ApplicationModal)  # 隐藏父窗口
        self.setFixedSize(600, 480)
        
        self.table = None
        self.button_export = None
        self.model = None
        
        self.load_data()
        self.log_dialog()
    
    def log_dialog(self):
        """
        日志弹窗
        :return:
        """
        self.table = QTableView(self)
        self.table.resize(600, 400)
        self.table.setModel(self.model)
        self.table.setEditTriggers(QTableView.NoEditTriggers)  # 设置表单不可编辑
        self.table.setSelectionMode(QTableView.NoSelection)  # 设置表单不可选中
        self.table.resizeColumnsToContents()  # 列根据内容调整大小
        self.table.resizeRowsToContents()  # 行根据内容调整大小
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)  # 表单自适应
        self.button_export = QPushButton("导出日志", self)
        self.button_export.move(220, 415)
    
    def load_data(self):
        """
        使用自带的QSqlQueryModel方法进行数据库查询
        :return:
        """
        db = QSqlDatabase.addDatabase("QSQLITE")  # 选着数据库类型
        db.setDatabaseName("./sys_db.db")
        db.open()
        self.model = QSqlQueryModel()
        self.model.setQuery(
            """select tb1.id,tb1.sname,tb2.clocktime,tb2.latetime from
             staff_tb as tb1 join logcat_tb as tb2 on tb1.id = tb2.id""")
        self.model.setHeaderData(0, Qt.Horizontal, "ID")
        self.model.setHeaderData(1, Qt.Horizontal, "姓名")
        self.model.setHeaderData(2, Qt.Horizontal, "打卡时间")
        self.model.setHeaderData(3, Qt.Horizontal, "迟到时长")


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
        self.button_login.clicked.connect(self.contrast)
    
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
        if self.name_edit.text() and self.passwd_edit.text():
            self.admin_name = load_admin(self.name_edit.text(), self.passwd_edit.text())
            if self.admin_name:
                self.close()
                return self.admin_name
            else:
                self.name_edit.clear()
                self.passwd_edit.clear()
                QMessageBox.information(self, "提示", "用户名或密码错误", QMessageBox.Yes)


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
        self.activity()
    
    def activity(self):
        self.button_next.clicked.connect(self.insert_data)
    
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
    
    def insert_data(self):
        """
        插入员工数据
        :return:
        """
        if self.id_edit.text() and self.name_edit.text() and self.department_edit.text():
            # insert_staff(self.id_edit.text(), self.name_edit.text(), self.department_edit.text())
            self.close()
            return self.id_edit.text()
        else:
            pass
            # QMessageBox.information(self, "提示", "输入内容不能为空", QMessageBox.Yes)


lock = QMutex()  # 创建进程锁


class ThreadIntoDB(QThread):
    def __init__(self, idn=None, parent=None):
        super().__init__(parent)
        self.id = idn
    
    def run(self):
        lock.lock()
        pics = os.listdir(Path_face + self.id)
        feature_list = []
        feature_average = []
        for i in range(len(pics)):
            pic_path = Path_face + self.id + "/" + pics[i]
            print("读取成功：", pic_path)
            img = cv2.imread(pic_path)  # 读入图片
            img_gray = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)  # 处理图片颜色空间转换为RGB
            dets = detector(img_gray, 1)
            if len(dets) != 0:  # 检测是否有人脸
                shape = predictor(img_gray, dets[0])  # 检测人脸特征点
                face_descriptor = facerec.compute_face_descriptor(img_gray, shape)  # 通过特征点获取人脸描述子
                feature_list.append(face_descriptor)  # 把人脸描述子保存在list中
            else:
                face_descriptor = 0
                print("未在照片中识别到人脸")
        if len(feature_list) > 0:
            for j in range(128):  # 128维度 ，防止越界
                feature_average.append(0)
                for i in range(len(feature_list)):
                    feature_average[j] += feature_list[i][j]
                feature_average[j] = (feature_average[j]) / len(feature_list)  # 对齐
            insert_face(self.id, feature_average)  # 插入数据库
        lock.unlock()


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
