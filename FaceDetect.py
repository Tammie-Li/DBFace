# -*- coding: utf-8 -*-
import sys
import cgitb
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QApplication, QDesktopWidget
from UI.Framelesswindow import FramelessWidget


# 标题栏样式
Style = """
/*标题栏颜色*/
TitleBar {
    background: "#27AAE1";
}

#TitleBar_buttonClose {
    /*需要把右侧的关闭按钮考虑进去*/
}

/*最小化、最大化、还原按钮*/
TitleBar > QPushButton {
    background: "#27AAE1";
}
TitleBar > QPushButton:hover {
    background: #89c4f4;
}
TitleBar > QPushButton:pressed {
    background: "#27AAE1";
}

/*关闭按钮*/
#TitleBar_buttonClose:hover {
    color: white;
    background: rgb(232, 17, 35);
}

#TitleBar_buttonClose:pressed {
    color: white;
    background: rgb(165, 69, 106);
}

/*鼠标悬停颜色*/
HistoryPanel::item:hover {
    background: rgb(52, 52, 52);
}
"""


if __name__ == '__main__':
    sys.excepthook = cgitb.enable(1, None, 5, '')
    app = QApplication(sys.argv)
    app.setStyleSheet(Style)
    desk = QDesktopWidget()
    screen = desk.screenGeometry()
    w = FramelessWidget()
    size = w.geometry()
    w.move((screen.width() - size.width()) / 2,
                  (screen.height() - size.height()) / 2)
    w.setObjectName("MainWindow")
    w.setStyleSheet("#MainWindow{background-color: #27AAE1}")
    w.show()
    w.setWindowIcon(QIcon('icon.ico'))
    sys.exit(app.exec_())