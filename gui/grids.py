import sys
import os

from PyQt5.QtWidgets import (QApplication, QMainWindow, QAction,
                            QComboBox, QWidget, QAbstractButton,
                            QGridLayout, QHBoxLayout, QVBoxLayout, 
                            QScrollArea, QDockWidget, QLabel,
                            QLayout)
from PyQt5.QtGui import (QPixmap, QPainter)
from PyQt5.QtCore import (Qt, QSize,pyqtSignal, QRect)

class MediaButton(QAbstractButton):
    def __init__(self, pixmap, parent=None, width=200, height=112 ):
        super(MediaButton, self).__init__(parent)
        self.pixmap = QPixmap(pixmap)
        self.setSize( width, height )

    def setSize( self, w, h ):
        self.setWidth( w )
        self.setHeight( h )
        
    def setWidth( self, w ):
        self.w = w

    def setHeight( self, h ):
        self.h = h
        
    def sizeHint(self):
        return QSize(self.w, self.h)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.drawPixmap(0, 0, self.width(), self.height(), self.pixmap)

    def dpaintEvent(self, event):
        painter = QPainter(self)
        painter.drawPixmap(event.rect(), self.pixmap)

    def pic_change(self, pixmap):
        self.pixmap = QPixmap(pixmap)

    @property
    def path( self ):
        return self._media_path

    @path.setter
    def path( self, value ):
        self._media_path = value
        
class Gallery( QWidget ):
    def __init__( self, parent = None, objectName = None ):
        super( Gallery, self ).__init__( parent, objectName = objectName )
        self.layout = QGridLayout()
        self.layout.setContentsMargins( 0,0,0,0)
        self.layout.setSizeConstraint( QLayout.SizeConstraint.SetFixedSize )
        self.setLayout( self.layout )
        self.buttons = []

        default_style = '''
        QWidget{
        background-color: black;
        }
        '''
        self.style( default_style )

        self.clear()
        self.refresh()
        
    def style( self, style ):
        self.setStyleSheet( style )

    def append( self, img, media = None ):
        button = MediaButton( img )
        button.path = media
        self.buttons.append( button )

    def clear( self ):
        while self.layout.count():
            child = self.layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

    def refresh( self, mod = 4 ):
        row = 0
        col = 0
        for i, button in enumerate( self.buttons ):
            if col > mod:
                row=i+1
                col=0
            self.layout.addWidget( button, row, col )
            col+=1
      

class gui(QMainWindow):
    def __init__(self):
        super().__init__()
        #self.ui_init()
        self.gallery=Gallery()
        img_path = "out.gif"
        for x in range( 100 ):
            self.gallery.append( img_path )
        self.gallery.refresh()

        self.scroll = QScrollArea()
        self.scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scroll.setWidgetResizable(False)
        self.scroll.setWidget(self.gallery)

        self.setCentralWidget(self.scroll)

        self.setGeometry(600, 600, 600, 600)
        self.show()

if __name__ == '__main__':
    app = QApplication([])
    ui = gui()
    sys.exit(app.exec_())
