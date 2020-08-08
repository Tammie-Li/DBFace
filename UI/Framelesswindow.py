# -*- coding: utf-8 -*-
import sys
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPainter, QPen, QColor, QEnterEvent, QPixmap, QFont
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton, QHBoxLayout, QComboBox, QFileDialog
import cv2 as cv
from PIL import Image
from UI.titlebar import TitleBar
from algorithm import transform
from algorithm.model.DBFace import DBFace
import torch
import algorithm.common as common


__Author__ = 'Hongxin Li'
__Copyright__ = 'Copyright (c) 2020'

LEFT = 1
TOP = 2
RIGHT = 4
BOTTOM = 8
LEFTTOP = LEFT | TOP
RIGHTTOP = RIGHT | TOP
LEFTBOTTOM = LEFT | BOTTOM
RIGHTBOTTOM = RIGHT | BOTTOM

HAS_CUDA = torch.cuda.is_available()


class FramelessBase():

    Margins = 0
#第一次显示时边框的宽度
    BaseClass = QWidget

    def __init__(self, *args, **kwargs):
        super(FramelessBase, self).__init__(*args, **kwargs)
        self.dragParams = {'type': 0, 'x': 0,
                           'y': 0, 'margin': 0, 'draging': False}
        self.originalCusor = None
        self.setMouseTracking(True)

        # 设置无边框
        self.setWindowFlags(self.windowFlags() | Qt.FramelessWindowHint)

    def isResizable(self):
        """是否可调整
        """
        return self.minimumSize() != self.maximumSize()

    def getEdge(self, pos):
        """返回点与边距接触的边的方向
        :param pos:
        """
        rect = self.rect()
        edge = 0
        if not self.isResizable():
            return edge
        if pos.x() <= rect.left() + self.Margins:
            edge |= LEFT
        elif pos.x() >= rect.right() - self.Margins:
            edge |= RIGHT
        if pos.y() <= rect.top() + self.Margins:
            edge |= TOP
        elif pos.y() >= rect.bottom() - self.Margins:
            edge |= BOTTOM
        return edge

    def adjustCursor(self, edge):
        """根据边方向调整光标样式
        :param edge:
        """
        cursor = None
        if edge in (TOP, BOTTOM):
            cursor = Qt.SizeVerCursor
        elif edge in (LEFT, RIGHT):
            cursor = Qt.SizeHorCursor
        elif edge in (LEFT | TOP, RIGHT | BOTTOM):
            cursor = Qt.SizeFDiagCursor
        elif edge in (TOP | RIGHT, BOTTOM | LEFT):
            cursor = Qt.SizeBDiagCursor
        if cursor and cursor != self.cursor():
            self.setCursor(cursor)

    def eventFilter(self, obj, event):
        """事件过滤器,用于解决鼠标进入其它控件后还原为标准鼠标样式
        """
        if isinstance(event, QEnterEvent):
            self.setCursor(self.originalCusor or Qt.ArrowCursor)
        return self.BaseClass.eventFilter(self, obj, event)

    def paintEvent(self, event):
        """由于是全透明背景窗口,重绘事件中绘制透明度为1的难以发现的边框,用于调整窗口大小
        """
        self.BaseClass.paintEvent(self, event)
        painter = QPainter(self)
        painter.setPen(QPen(QColor(255, 255, 255, 1), 2 * self.Margins))
        painter.drawRect(self.rect())

    def showEvent(self, event):
        """第一次显示时设置控件的layout的边距
        :param event:
        """
        layout = self.layout()
        if self.originalCusor == None and layout:
            self.originalCusor = self.cursor()
            layout.setContentsMargins(
                self.Margins, self.Margins, self.Margins, self.Margins)
            # 对所有子控件增加事件过滤器
            for w in self.children():
                if isinstance(w, QWidget):
                    w.installEventFilter(self)
        self.BaseClass.showEvent(self, event)

    def mousePressEvent(self, event):
        """鼠标按下设置标志
        :param event:
        """
        if not self.isResizable() or self.childAt(event.pos()):
            return
        self.dragParams['x'] = event.x()
        self.dragParams['y'] = event.y()
        self.dragParams['globalX'] = event.globalX()
        self.dragParams['globalY'] = event.globalY()
        self.dragParams['width'] = self.width()
        self.dragParams['height'] = self.height()
        if event.button() == Qt.LeftButton and self.dragParams['type'] != 0 \
                and not self.isMaximized() and not self.isFullScreen():
            self.dragParams['draging'] = True

    def mouseReleaseEvent(self, event):
        """释放鼠标还原光标样式
        :param event:
        """
        self.dragParams['draging'] = False
        self.dragParams['type'] = 0

    def mouseMoveEvent(self, event):
        """鼠标移动用于设置鼠标样式或者调整窗口大小
        :param event:
        """
        if self.isMaximized() or self.isFullScreen() or not self.isResizable():
            return

        # 判断鼠标类型
        cursorType = self.dragParams['type']
        if not self.dragParams['draging']:
            cursorType = self.dragParams['type'] = self.getEdge(event.pos())
            self.adjustCursor(cursorType)

        # 判断窗口拖动
        if self.dragParams['draging']:
            x = self.x()
            y = self.y()
            width = self.width()
            height = self.height()

            if cursorType & TOP == TOP:
                y = event.globalY() - self.dragParams['margin']
                height = self.dragParams['height'] + \
                    self.dragParams['globalY'] - event.globalY()
            if cursorType & BOTTOM == BOTTOM:
                height = self.dragParams['height'] - \
                    self.dragParams['globalY'] + event.globalY()
            if cursorType & LEFT == LEFT:
                x = event.globalX() - self.dragParams['margin']
                width = self.dragParams['width'] + \
                    self.dragParams['globalX'] - event.globalX()
            if cursorType & RIGHT == RIGHT:
                width = self.dragParams['width'] - \
                    self.dragParams['globalX'] + event.globalX()

            minw = self.minimumWidth()
            maxw = self.maximumWidth()
            minh = self.minimumHeight()
            maxh = self.maximumHeight()
            if width < minw or width > maxw or height < minh or height > maxh:
                return

            self.setGeometry(x, y, width, height)


class FramelessWidget(QWidget, FramelessBase):

    BaseClass = QWidget

    def __init__(self, *args, **kwargs):
        super(FramelessWidget, self).__init__(*args, **kwargs)

        self.resize(1280, 828)
        self.setStyleSheet("back")
        v_layout = QVBoxLayout(self)

        box = QWidget(self)
        box.setMaximumHeight(70)
        h_layout = QHBoxLayout(box)
        v_layout.setSpacing(0)

        self.image_show = QLabel(self, alignment=Qt.AlignCenter)
        self.image_show.setText("请先选择要检测的图像")
        self.image_show.setStyleSheet("QLabel{background-color:gray}")
        self.image_show.setFont(QFont("宋体", 25))

        button_select = QPushButton(self)
        button_select.setText("选择图片")
        button_select.clicked.connect(self.select_image)

        button_start = QPushButton(self)
        button_start.setText("开始检测")
        button_start.clicked.connect(self.tran_image)

        self.combox = QComboBox(self)
        self.combox.setFixedHeight(button_start.height())
        self.combox.addItem("图片模式")
        self.combox.addItem("摄像头模式")
        self.combox.currentIndexChanged.connect(self.tran_camera)

        h_layout.addWidget(button_select)
        h_layout.addWidget(button_start)
        h_layout.addWidget(self.combox)

        # 添加自定义标题栏
        v_layout.addWidget(TitleBar(self, title='基于DBFace的人脸识别                    Designed by Tammie li'))
        v_layout.addWidget(self.image_show)
        v_layout.addWidget(box)

        self.dbface = DBFace()
        self.dbface.eval()
        self.FLAG = 0

        if HAS_CUDA:
            self.dbface.cuda()
        self.dbface.load("algorithm//model//dbface.pth")

    def select_image(self):
        file = QFileDialog.getOpenFileName()[0]
        self.image = QPixmap(file)
        self.im_tran = file
        self.image_show.setPixmap(self.image)
    
    def tran_image(self):
        image = transform.image_demo(self.dbface, self.im_tran)
        img = cv.cvtColor(image, cv.COLOR_BGR2RGB)
        im = Image.fromarray(img)
        image = im.toqpixmap()
        self.image_show.setPixmap(image)

    def tran_camera(self):
        if self.combox.currentText()=='摄像头模式':
            cap = cv.VideoCapture(0)
            cap.set(cv.CAP_PROP_FRAME_WIDTH, 1280)
            cap.set(cv.CAP_PROP_FRAME_HEIGHT, 720)   

            ok, frame = cap.read()
            while ok:
                ok, frame = cap.read()
                objs = transform.detect(self.dbface, frame)
            
                for obj in objs:
                    common.drawbbox(frame, obj)
                img = cv.cvtColor(frame, cv.COLOR_BGR2RGB)
                im = Image.fromarray(img)
                image = im.toqpixmap()
                self.image_show.setPixmap(image)
                cv.imshow("DBFace", frame)
                key = cv.waitKey(1) & 0xFF
                if key == ord('q'):
                    break
                if self.combox.currentText()=='图片模式':
                    self.image_show.setText("请先选择要检测的图像")
                    self.image_show.setFont(QFont("宋体", 25))
                    break


            

    
        

