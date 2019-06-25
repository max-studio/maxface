import sys
from PyQt5 import QtWidgets
from PyQt5.QtWidgets import (QMenuBar,QAction,QVBoxLayout,QHBoxLayout,QTableWidget,
                             QTextEdit,QLabel,QHeaderView,QApplication,QInputDialog,
                             QMessageBox)
from PyQt5.QtCore import Qt,QTimer
from PyQt5.QtGui import QPixmap,QIcon,QColor,QFont,QBrush,QImage
import sip
from time import localtime,strftime
import cv2
import numpy as np
import dlib
import zlib
import io,os
from skimage import io as iio
import sqlite3
import _thread


Path = r"C:\Program Files (x86)\Microsoft Visual Studio\Shared\Python36_64\Lib\site-packages\cv2\data\haarcascade_frontalface_default.xml"
face_detector = cv2.CascadeClassifier(Path)
Path_face = "./data/face_img_database/"
facerec = dlib.face_recognition_model_v1("./model/dlib_face_recognition_resnet_model_v1.dat")
# Dlib 预测器
detector = dlib.get_frontal_face_detector()
predictor = dlib.shape_predictor('./model/shape_predictor_68_face_landmarks.dat')

def return_euclidean_distance(feature_1, feature_2):
    feature_1 = np.array(feature_1)
    feature_2 = np.array(feature_2)
    dist = np.sqrt(np.sum(np.square(feature_1 - feature_2)))
    print("欧式距离: ", dist)

    if dist > 0.4:
        return "diff"
    else:
        return "same"
    
class Ui_MainWindow(QtWidgets.QWidget):
    def __init__(self,parent=None):
        super(Ui_MainWindow,self).__init__(parent)
        self.resize(920, 560)
        self.setWindowTitle("Max打卡系统--V0.1")
        self.timer_camera = QTimer()
        self.cap = cv2.VideoCapture()
        
        self.set_ui()
        self.clicked_activity()
        self.init_info_text()
        self.init_database()
        self.init_data()
        
    def init_data(self):
        self.CAM_NUM = 0
        self.id = -1
        self.name = ""
        self.face_feature = ""
        self.pic_num = 0
        self.flag_registed = False
        self.puncard_time = "08:00:00"
        self.load_data_base(1)
        self.sign = 1
        
    def set_ui(self):
        self.menu_bar = QMenuBar(self)#菜单栏
        self.menu_bar.addSeparator()
        self.registerMenu = self.menu_bar.addMenu("人脸录入")
        self.puncardMenu = self.menu_bar.addMenu("刷脸签到")
        self.logcatMenu = self.menu_bar.addMenu("打卡日志")
        
        #子菜单
        self.new_entry = QAction("新建录入")
        self.new_entry.setShortcut("Ctrl+s")
        self.new_entry.setIcon(QIcon(r"./icon/plus.ico"))
        self.registerMenu.addAction(self.new_entry)
        self.registerMenu.addSeparator()
        self.finish_entry = QAction("完成录入")
        self.finish_entry.setIcon(QIcon(r"./icon/checked.ico"))
        self.registerMenu.addAction(self.finish_entry)
        self.finish_entry.setEnabled(False)
        self.start_check_in = QAction("开始签到")
        self.start_check_in.setIcon(QIcon(r"./icon/arrows2.ico"))
        self.puncardMenu.addAction(self.start_check_in)
        self.puncardMenu.addSeparator()
        self.finish_check_in = QAction("完成签到")
        self.finish_check_in.setIcon(QIcon(r"./icon/arrowst.ico"))
        self.puncardMenu.addAction(self.finish_check_in)
        self.finish_check_in.setEnabled(False)
        self.open_log = QAction("打开日志")
        self.open_log.setIcon(QIcon(r"./icon/arrows4.ico"))
        self.logcatMenu.addAction(self.open_log)
        self.logcatMenu.addSeparator()
        self.close_log = QAction("关闭日志")
        self.close_log.setIcon(QIcon(r"./icon/arrows3.ico"))
        self.logcatMenu.addAction(self.close_log)
        self.close_log.setEnabled(False)
       
        self.vlayout = QVBoxLayout()
        self.vlayout.addWidget(self.menu_bar)
        self.hlayout = QHBoxLayout()
        
        self.vlayout.addLayout(self.hlayout)
        # self.setLayout(self.vlayout)
        self.setLayout(self.vlayout)
        
    def clicked_activity(self):
        # 信号槽
        self.new_entry.triggered.connect(self.prompt_information)
        self.timer_camera.timeout.connect(lambda : self.show_camera(self.sign))
        self.finish_entry.triggered.connect(lambda : self.close_camera(self.sign))
        self.start_check_in.triggered.connect(self.punch_card_cap)
        self.finish_check_in.triggered.connect(lambda : self.close_camera(self.sign))
        self.open_log.triggered.connect(self.open_log_clicked)
        self.close_log.triggered.connect(self.close_log_clicked)
        
    def init_info_text(self): #显示信息
        self.result_text = QTextEdit(self)
        self.result_text.resize(100, 60)
        self.result_text.setStyleSheet("background:LightSkyBlue")
        # self.result_text.setTextBackgroundColor(QColor(255,165,0))
        self.result_text.setReadOnly(True)
        # pal = self.result_text.viewport().palette()
        # pal.setColor(QPalette.Base,pal.color(QPalette.Background))
        # self.result_text.viewport().setPalette(pal)
       
        text = "\r\n初始时间:"+self.get_date_time()+"\r\n"
        self.result_text.setHtml("<font color = 'red' size = '6'><red><U>"+text+"</U></font>")
        # self.result_text.append("")
        
        self.hlayout.addWidget(self.result_text)
        self.add_image()
        
    def add_image(self , id=1): #首页图片
        self.image = QLabel(self)
        # self.image.setAutoFillBackground(False)
        self.image.setPixmap(QPixmap(r"G:\githublocal\drawable\MaXlogo.jpg").scaled(600, 500))
        if id:
            self.hlayout.addWidget(self.image)
        else:
            self.hlayout.removeWidget(self.table)
            sip.delete(self.table)
            self.hlayout.addWidget(self.image)
    
    def open_log_clicked(self): #查看打卡情况
        self.open_log.setEnabled(False)
        self.close_log.setEnabled(True)
        self.table = QTableWidget(10000,4)
        self.table.resize(600,500)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setSelectionMode(QTableWidget.NoSelection)
        header = ["学号","姓名","打卡时间","是否有效"]
        self.table.setHorizontalHeaderLabels(header)
        for index in range(self.table.columnCount()):
            headItem = self.table.horizontalHeaderItem(index)
            headItem.setFont(QFont("song", 12, QFont.Bold))
            headItem.setForeground(QBrush(Qt.gray))
            headItem.setTextAlignment(Qt.AlignLeft | Qt.AlignVCenter)
            
        self.table.resizeColumnsToContents()
        self.table.resizeRowsToContents()
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        # self.table.resizeSection(600,500)
        self.hlayout.removeWidget(self.image)
        sip.delete(self.image)
        self.hlayout.addWidget(self.table)
        
        # 插入数据
        # for i,id in enumerate(self.logcat_id):
        #     self.table.setItem(i,0,str(id))
        #     self.table.setItem(i, 1, self.logcat_name[i])
        #     self.table.setItem(i, 2, self.logcat_datetime[i])
        #     self.table.setItem(i, 3, self.logcat_late)
        
    def close_log_clicked(self): # 关闭日志
        self.open_log.setEnabled(True)
        self.close_log.setEnabled(False)
        self.close_id = 0
        self.add_image(0)
   
    def get_date_time(self): #获取时间
        datetime = strftime("%Y-%m-%d %H:%M:%S",localtime())
        # print(datetime)
        return "["+datetime+"]"
    
    def new_create_time(self,n): # 检查相机，计时
        print("运行")
        if n == 1:
            self.new_entry.setEnabled(False)
            self.finish_entry.setEnabled(True)
    
        if self.timer_camera.isActive() == False:
            
            flag = self.cap.open(self.CAM_NUM)
            if flag == False:
                msg = QtWidgets.QMessageBox.warning(self, u"Warning", u"请检测相机与电脑是否连接正确",
                                                    buttons=QtWidgets.QMessageBox.Ok,
                                                    defaultButton=QtWidgets.QMessageBox.Ok)
            else:
                self.timer_camera.start(30)
        else:
            self.timer_camera.stop()
            self.cap.release()
            self.image.setPixmap(QPixmap(r"G:\githublocal\drawable\MaXlogo.jpg").scaled(600, 500))
        
    def show_camera(self , n):  # 识别人脸
        # with self.cap.isOpened():
        
        # read()
        # 返回两个值：
        #    一个布尔值true/false，用来判断读取视频是否成功/是否到视频末尾
        #    图像对象，图像的三维矩阵
        flag, self.im_rd = self.cap.read()
        key = cv2.waitKey(10)
        #人脸数
        dets = detector(self.im_rd, 1)
        # 检测到人脸
        if len(dets) != 0:
            biggest_face = dets[0]
            # 占比最大的脸
            max_area = 0
            for det in dets:
                w = det.right() - det.left()
                h = det.top() - det.bottom()
                if w * h > max_area:
                    biggest_face = det
                    max_area = w * h
                    # 绘制矩形框
            cv2.rectangle(self.im_rd, tuple([biggest_face.left(), biggest_face.top()]),
                          tuple([biggest_face.right(), biggest_face.bottom()]),
                          (255, 0, 0), 2)
        show = cv2.resize(self.im_rd, (600, 500))
        show = cv2.cvtColor(show, cv2.COLOR_BGR2RGB)
        showImage = QImage(show.data, show.shape[1], show.shape[0], QImage.Format_RGB888)
        self.image.setPixmap(QPixmap.fromImage( showImage ))

        # show = cv2.resize(self.im_rd, (600, 500))
        # show = cv2.cvtColor(show, cv2.COLOR_BGR2RGB)
        # faces = face_detector.detectMultiScale(show, 1.3, 5)  # 1.image表示的是要检测的输入图像# 2.objects表示检测到的人脸目标序列# 3.scaleFactor表示每次图像尺寸减小的比例
        # for (x, y, w, h) in faces:
        #     # 画矩形
        #     print("123")
        #     cv2.rectangle(show, (x, y), (x + w, y + w), (255, 0, 0))
        #     showImage = QImage(show.data, show.shape[1], show.shape[0], QImage.Format_RGB888)
        #     self.image.setPixmap(QPixmap.fromImage(showImage))
        if n == 1:# 录入人脸
            # shape = predictor(self.im_rd,biggest_face)
                    # features_cap = facerec.compute_face_descriptor(self.im_rd, shape)
                    #
                    # # 对于某张人脸，遍历所有存储的人脸特征
                    # for i, knew_face_feature in enumerate(self.knew_face_feature):
                    #     # 将某张人脸与存储的所有人脸数据进行比对
                    #     compare = return_euclidean_distance(features_cap, knew_face_feature)
                    #     if compare == "same":  # 找到了相似脸
                    #         self.result_text.append(self.get_date_time + "学号:" + str(self.knew_id[i])
                    #                                  + " 姓名:" + self.knew_name[i] + " 的人脸数据已存在\r\n")
                    #         self.flag_registed = True
                    #         # self.OnFinishRegister()
                    # print(features_known_arr[i][-1])
            
            face_height = biggest_face.bottom() - biggest_face.top()
            face_width = biggest_face.right() - biggest_face.left()
            print(int(face_height),int(face_width))
            im_blank = np.zeros((face_height, face_width, 3), np.uint8)
            try:
                for ii in range(face_height):
                    for jj in range(face_width):
                        im_blank[ii][jj] = self.im_rd[int(biggest_face.top()) + ii][int(biggest_face.left()) + jj]
                self.pic_num += 1
                # cv2.imwrite(Path_face+self.name +"/img_face_" + str(self.pic_num) + ".jpg",im_blank)#中文路径无法存储

                print(self.name)
                if len(self.name) > 0:
                    cv2.imencode('.jpg', im_blank)[1].tofile(
                    Path_face + self.name + "/img_face_" + str(self.pic_num) + ".jpg")
                    print("写入本地：", str(Path_face + self.name) + "/img_face_" + str(self.pic_num) + ".jpg")
            except:
                print("保存照片异常,请对准摄像头")
                
        # elif n == 2:#识别人脸并打卡
        #     print("签到成功")
        #     shape = predictor(self.im_rd, biggest_face)
        #     features_cap = facerec.compute_face_descriptor(self.im_rd, shape)
        #     for i, knew_face_feature in enumerate(self.knew_face_feature):
        #         # 将某张人脸与存储的所有人脸数据进行比对
        #         compare = return_euclidean_distance(features_cap, knew_face_feature)
        #         if compare == "same":  # 找到了相似脸
        #             print("same")
            #         # flag = 0
            #         # nowdt = self.getDateAndTime()
            #         # for j,logcat_name in enumerate(self.logcat_name):
            #         #     if logcat_name == self.knew_name[i] and nowdt[0:nowdt.index(" ")] == self.logcat_datetime[j][0:self.logcat_datetime[j].index(" ")]:
            #         #         # self.infoText.AppendText(nowdt+"学号:"+ str(self.knew_id[i])
            #         #         #                  + " 姓名:" + self.knew_name[i] + " 签到失败,重复签到\r\n")
            #         #         flag = 1
            #         #         break
            #
            #         if flag == 1:
            #             break
            #
            #         # if nowdt[nowdt.index(" ")+1:-1] <= self.puncard_time:
            #             # self.infoText.AppendText(nowdt + "学号:" + str(self.knew_id[i])
            #             #                      + " 姓名:" + self.knew_name[i] + " 签到时间为8点以后\r\n")
            #             # self.insertARow([self.knew_id[i],self.knew_name[i],nowdt,"否"],1)
            #             pass
            #         else:
            #             # self.infoText.AppendText(nowdt + "学号:" + str(self.knew_id[i])
            #             #                          + " 姓名:" + self.knew_name[i] + " 成功签到\r\n")
            #             # self.insertARow([self.knew_id[i], self.knew_name[i], nowdt, "是"], 2)
            #         # self.loadDataBase(2)
            #             print("签到成功")
            #             pass
            #         break

            # if self.start_punchcard.IsEnabled():
            #     # self.bmp.SetBitmap(wx.Bitmap(self.pic_index))
            #     pass

    def close_camera(self,n):
        if n == 1:
            self.finish_entry.setEnabled(False)
            self.new_entry.setEnabled(True)
        elif n == 2:
            self.start_check_in.setEnabled(True)
            self.finish_check_in.setEnabled(False)
        self.sign = 1
        if self.cap.isOpened():
            self.cap.release()
        if self.timer_camera.isActive():
            self.timer_camera.stop()
        self.image.setPixmap(QPixmap(r"G:\githublocal\drawable\MaXlogo.jpg").scaled(600, 500))
        self.memory_face()
    def prompt_information(self): #提示输入信息
        
        try:
            self.id,ok  = QInputDialog.getInt(self,"提示","请输入学号:")
            if ok :
                self.load_data_base(1)
                print(self.id)
            #TODO 与数据库中数据进行比较，如果存在，这提示学号已存在
                for knew_id in self.knew_id:
                    print(knew_id)
                    if self.id == knew_id:
                        QMessageBox.warning("学号重复","学号已存在，请重新输入",QMessageBox.Yes|QMessageBox.No,QMessageBox.Yes)
                        
            #TODO 如果数据库中不存在，着进行输入姓名
            if self.name == "" or self.id != -1:
                self.name,ok = QInputDialog.getText(self, "温馨提示","请输入你的姓名:")
                print(self.name)
                # pass
                os.makedirs(Path_face + self.name)
            else:
                QMessageBox.warning("无姓名", "请重新输入", QMessageBox.Yes | QMessageBox.No, QMessageBox.Yes)
    
            self.new_create_time(self.sign)
        except:
            print("出錯")
            pass
            
    def punch_card_cap(self): # 打卡
        self.start_check_in.setEnabled(False)
        self.finish_check_in.setEnabled(True)
        self.sign = 2
        self.new_create_time(self.sign)
        
    def memory_face(self):
        if self.pic_num > 0:
            pics = os.listdir(Path_face + self.name) #返回指定目录下的文件列表
            feature_list = []
            feature_average = []
            for i in range(len(pics)):
                pic_path = Path_face + self.name + "/" + pics[i]
                print("正在读的人脸图像：", pic_path)
                img = iio.imread(pic_path)
                img_gray = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
                dets = detector(img_gray, 1)
                if len(dets) != 0:
                    shape = predictor(img_gray, dets[0])
                    face_descriptor = facerec.compute_face_descriptor(img_gray, shape)
                    feature_list.append(face_descriptor)
                else:
                    face_descriptor = 0
                    print("未在照片中识别到人脸")
            if len(feature_list) > 0:
                for j in range(5):
                    #防止越界
                    feature_average.append(0)
                    for i in range(len(feature_list)):
                        feature_average[j] += feature_list[i][j]
                    feature_average[j] = (feature_average[j]) / len(feature_list)
                # self.insert_Row([self.id,self.name,feature_average],1)
                text = self.get_date_time()+"学号:"+str(self.id)+" 姓名:"+self.name+" 的人脸数据已成功存入\r\n"
                # self.result_text.append("<font color = 'red' size = '6'><red><U>" + text + "</U></font>")
                print(text)
                # _thread.exit()

        else:
            os.rmdir(Path_face + self.name)
            print("已删除空文件夹",Path_face + self.name)
        # self.init_data()
    def init_database(self):
        conn = sqlite3.connect("inspurer.db")  # 建立数据库连接
        cur = conn.cursor()  # 得到游标对象
        cur.execute('''create table if not exists student_info
                (sname text not null,
                id int not null primary key,
                face_feature array not null)''')
        cur.execute('''create table if not exists logcat
                 (datetime text not null,
                 id int not null,
                 sname text not null,
                 late text not null)''')
        cur.close()
        conn.commit()
        conn.close()
        
    def adapt_array(self,arr):
        
        out = io.BytesIO()
        np.save(out, arr)
        out.seek(0)
        dataa = out.read()
        # 压缩数据流
        return sqlite3.Binary(zlib.compress(dataa, zlib.Z_BEST_COMPRESSION))

    def convert_array(self,text):
        out = io.BytesIO(text)
        out.seek(0)

        dataa = out.read()
        # 解压缩数据流
        out = io.BytesIO(zlib.decompress(dataa))
        return np.load(out)
    
    def insert_Row(self,Row,type):
        conn = sqlite3.connect("inspurer.db")  # 建立数据库连接
        cur = conn.cursor()  # 得到游标对象
        if type == 1:
            print(Row[0],Row[1])
            cur.execute("insert into student_info (id,sname,face_feature) values(?,?,?)",
                        (Row[0], Row[1],self.adapt_array(Row[2])))
            print("写人脸数据成功")
        if type == 2:
            cur.execute("insert into logcat (id,sname,datetime,late) values(?,?,?,?)",
                        (Row[0],Row[1],Row[2],Row[3]))
            print("写日志成功")
            pass
        cur.close()
        conn.commit()
        conn.close()
        pass
    
    def load_data_base(self,type):
        conn = sqlite3.connect("inspurer.db")  # 建立数据库连接
        cur = conn.cursor()  # 得到游标对象
 
        if type == 1:
            self.knew_id = []
            self.knew_name = []
            self.knew_face_feature = []
            cur.execute('select id,sname,face_feature from student_info')
            origin = cur.fetchall()
            for row in origin:
                print(row[0])
                self.knew_id.append(row[0])
                print(row[1])
                self.knew_name.append(row[1])
                print(self.convert_array(row[2]))
                self.knew_face_feature.append(self.convert_array(row[2]))
        if type == 2:
            self.logcat_id = []
            self.logcat_name = []
            self.logcat_datetime = []
            self.logcat_late = []
            cur.execute('select id,sname,datetime,late from logcat')
            origin = cur.fetchall()
            for row in origin:
                print(row[0])
                self.logcat_id.append(row[0])
                print(row[1])
                self.logcat_name.append(row[1])
                print(row[2])
                self.logcat_datetime.append(row[2])
                print(row[3])
                self.logcat_late.append(row[3])
        
if __name__ == '__main__':
    App = QApplication(sys.argv)
    ex = Ui_MainWindow()
    ex.show()
    sys.exit(App.exec_())

