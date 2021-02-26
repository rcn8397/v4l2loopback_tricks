#!/usr/bin/env python3
import os
import sys
import time
from PyQt5.QtCore    import QTimer, Qt, QEvent, pyqtSignal, QThread, QObject, QRect
from PyQt5.QtWidgets import QApplication, QMainWindow
from PyQt5.QtWidgets import QLabel, QGridLayout, QPushButton, QWidget, QComboBox, QScrollArea
from PyQt5.QtWidgets import QHBoxLayout, QVBoxLayout, QStyle, QFrame

# Setup imports from module
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from v4l2tricks.ffmpeg_if import DesktopScopeProcess
#from v4l2tricks.stream import desktop_stream

get_video_devices = lambda : [ dev for dev in os.listdir('/dev') if 'video' in dev ]

class StreamScope( QWidget ):
    resize_signal  = pyqtSignal(int)
    resolutions    = [ '640x480',
                       '720x480',
                       '1280x720' ]
    def __init__( self ):
        super().__init__()
        self.title_bar_h   = self.style().pixelMetric( QStyle.PM_TitleBarHeight )
        self.devices       = get_video_devices()
        self.device        = '/dev/{0}'.format( self.devices[0] )
        res                = self.resolutions[0].split( 'x' )
        self.res_w         = int( res[0])
        self.res_h         = int( res[1])
        self.stream_thread = QThread(parent=self)
        self.streamer      = DeskStreamer()
        self.streamer.moveToThread( self.stream_thread )
        self.streamer.finished.connect( self.stream_thread.quit )
        self.streamer.finished.connect( self.streamer.deleteLater )
        self.stream_thread.finished.connect( self.stream_thread.deleteLater )
        self.stream_thread.start()
        self.stream_thread.started.connect( self.streamer.long_running )

        self.setWindowTitle( self.__class__.__name__ )
        self.setGeometry( 0, 0, 640, 500 )

        self.init_layout()

        # Show the window
        self.show()


    def init_layout( self ):
        layout1 = QVBoxLayout()
        layout2 = QHBoxLayout()

        # Get video devices
        combo      = QComboBox( self )
        for i, device in enumerate( self.devices ):
            combo.addItem( device )
            if device == 'video20':
               combo.setCurrentIndex( i )
               self.device = '/dev/{0}'.format( device )
        combo.activated[str].connect( self.comboChanged )

        resolution = QComboBox( self )
        for res in self.resolutions:
            resolution.addItem( res )
        resolution.activated[str].connect( self.resolutionChanged )


        # Buttons
        self.stream_btn = QPushButton( self, objectName='stream_btn' )
        self.stream_btn.setText( 'Stream' )
        self.stream_btn.clicked.connect( self.stream )

        self.stop_btn = QPushButton( self, objectName='stop_btn' )
        self.stop_btn.setText( 'Stop' )
        self.stop_btn.clicked.connect( self.stop )

        self.frame = QFrame(self )
        style='''
        QPushButton{
            text-align:center;
        }
        QPushButton#stream_btn{
        background-color: orange;
        }
        QPushButton#stop_btn{
        background-color: red;
        }
        QFrame{
        background-color: #777777;
        border-bottom-right-radius: 10px;
        border-bottom-left-radius:  10px;
        }
        '''
        self.frame.setStyleSheet( style )

        layout2.addWidget( self.stream_btn )
        layout2.addWidget( self.stop_btn )
        layout2.addWidget( resolution )
        layout2.addWidget( combo )
        self.frame.setLayout( layout2 )
        self.frame.setFixedHeight( self.frame.height()*1.5 )

        self.viewfinder = QLabel()
        self.viewfinder.setStyleSheet( 'background-color: cyan; border:5px solid orange; background:transparent; padding:0px;' )
        self.viewfinder.setMinimumWidth( self.res_w )
        self.viewfinder.setMinimumHeight( self.res_h )
        self.viewfinder.setGeometry( QRect( self.frame.pos().x(), 0, self.res_w, self.res_h ) )

        layout1.addWidget( self.viewfinder )
        layout1.addWidget( self.frame )
        layout1.setContentsMargins( 0 ,0 ,0, 0 )
        self.setAttribute( Qt.WA_TranslucentBackground )
        self.setLayout( layout1 )
        self.update_frustum()

    def stream( self ):
        print( 'Started' )
        if not self.streamer.isStreaming():
            self.viewfinder.setStyleSheet( 'background-color: cyan; border:1px hidden red; background:transparent; ' )
            self.update_frustum()
            self.streamer.stream()

    def stop( self ):
        if self.streamer.isStreaming():
            print( 'Stopped' )
            self.viewfinder.setStyleSheet( 'background-color: cyan; border:5px solid orange; background:transparent; padding:0;' )
            self.streamer.stop()

    def comboChanged( self, text ):
        print( 'Combo changed: {0}'.format( text ) )
        self.stop()
        self.device = '/dev/{0}'.format( text )

    def resolutionChanged( self, text ):
        print( 'Resolution changed: {0}'.format( text ) )
        self.stop()
        res = text.split( 'x' )
        self.res_w = int( res[0] )
        self.res_h = int( res[1] )
        self.viewfinder.setMinimumWidth( self.res_w )
        self.viewfinder.setMinimumHeight( self.res_h )
        self.viewfinder.setGeometry( QRect( self.frame.pos().x(), 0, self.res_w, self.res_h ) )
        self.setGeometry( QRect( self.pos().x(), self.pos().y(), self.res_w, self.res_h ) )
        self.adjustSize()

    def update_frustum( self ):
        print( 'Window: {0}, {1}x{2}'.format( self.pos(), self.width(), self.height() ) )
        print( 'Status: {0}'.format( self.title_bar_h ) )
        print( 'Scope:  {0}, {1}x{2}'.format( self.viewfinder.pos(),self.viewfinder.width(), self.viewfinder.height() ) )
        print( 'Device: {0}'.format( self.device ) )
        self.streamer.x = self.pos().x() + self.viewfinder.pos().x() + 0
        self.streamer.y = self.pos().y() + self.viewfinder.pos().y() + self.title_bar_h + 5
        self.streamer.width  = self.viewfinder.width()
        self.streamer.height = self.viewfinder.height()
        self.streamer.device = self.device

    def moveEvent( self, event ):
        print( 'Moved' )
        self.stop()
        self.update_frustum()
        super().moveEvent(event)

    def resizeEvent(self, event = None):
        print( 'Resized' )
        self.stop()
        self.update_frustum()
        self.resize_signal.emit( 1 )

    def closeEvent( self, event ):
        self.thread_clean_up()
        super().closeEvent( event )

    def thread_clean_up( self ):
        print( 'Cleaning up thread' )
        self.streamer.exit()
        self.stream_thread.quit()
        self.stream_thread.wait()


class DeskStreamer( QObject ):
    finished = pyqtSignal()

    def __init__( self ):
        super(DeskStreamer, self).__init__()
        self._running = False
        self._exit    = False
        self.x        = 0
        self.y        = 0
        self.width    = 640
        self.height   = 480
        self.display  = None
        self.device   = '/dev/video20'

    def isStreaming( self ):
        return self._running

    def stream( self ):
        print( 'Stream called' )
        self._running = True

    def stop( self ):
        print( 'Stop called' )
        self._running = False

    def exit( self ):
        print( 'Exit called' )
        self._running = False
        self._exit = True

    def long_running( self ):
        while not self._exit:
            if self._running:
                print("Streamer: running" )
                self.debug_parameters()
                #time.sleep(1)
                self.start_streaming()

        self.finished.emit()
        print( '{0} finished'.format( __class__.__name__ ) )

    def debug_parameters( self ):
        print( '{0}: {1}'.format( 'x', self.x ) )
        print( '{0}: {1}'.format( 'y', self.y ) )
        print( '{0}: {1}'.format( 'width', self.width ) )
        print( '{0}: {1}'.format( 'height', self.height ) )
        print( self.device )

    def process_stream( self, stream ):
        while stream.alive and self._running:
            line  = stream.readline
            if line is not None:
                print( line )
        stream.stop()
        print( 'Bye' )

    def start_streaming( self ):
        self.display = ':1'
        try:
            self.display = os.environ[ 'DISPLAY' ]
        except KeyError as e:
            print( 'Could not detect DISPLAY variable (normally :0 or :1)' )
            pass

        stream = DesktopScopeProcess( self.x,
                                      self.y,
                                      self.width,
                                      self.height,
                                      self.display,
                                      self.device,
                                      True )

        self.process_stream( stream )


# Main
def main():
    app = QApplication( sys.argv )
    ss = StreamScope()
    sys.exit( app.exec_() )

# Standard biolerplate to call the main() function to begin the program
if __name__ == '__main__':
    main()
