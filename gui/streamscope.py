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
    resolutions    = [
        '320x200',  # CGA           0
        '320x240',  # QVGA          1
        '480x320',  # HVGA          2
        '640x480',  # VGA           3
        '720x480',  # 480p          4
        '800x480',  # WVGA          5
        '854x480',  # WVGA (NTSC+)  6
        '1024x576', # PAL+          7
        '1024x768', # XGA           8
        '1280x720', # HD            9
        '1280x768', # WXGA          10
        'Elastic',  # Elastic       11
    ]
    
    def __init__( self ):
        super().__init__()
        self.title_bar_h   = self.style().pixelMetric( QStyle.PM_TitleBarHeight )
        self.devices       = get_video_devices()
        self.device        = '/dev/{0}'.format( self.devices[0] )

        # Setup the default resolution for the app
        use_resolution = 4
        self.resolution_name = self.resolutions[ use_resolution ]
        res                = self.resolutions[ use_resolution ].split( 'x' )
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
        self.setGeometry( 0, 0, self.res_w, self.res_h )

        self.init_layout()

        self.setWindowFlags( self.windowFlags() # Keep existing flags
                             | Qt.WindowStaysOnTopHint 
        )

        
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
        resolution.setCurrentIndex( self.resolutions.index(self.resolution_name ) )

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
        background-color: white;
        }
        QFrame{
        background-color: #3E3E3E;
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
        self.frame.setFixedHeight( 40 )

        self.viewfinder = QLabel(self, objectName='view_finder')
        style='''
        QLabel{
        background-color: cyan;
        }
        QLabel#view_finder{
        border:5px solid orange;
        background:transparent;
        padding:0px;
        }
        '''
        self.viewfinder.setStyleSheet( style )
        self.viewfinder.setMinimumWidth( 0 )
        self.viewfinder.setMinimumHeight( 0 )
        self.viewfinder.setGeometry( QRect( self.frame.pos().x(), 0, self.res_w, self.res_h ) )
        layout1.addWidget( self.viewfinder )
        layout1.addWidget( self.frame )
        layout1.setSpacing(0)
        layout1.setContentsMargins( 0 ,0 ,0, 0 )
        self.setAttribute( Qt.WA_TranslucentBackground )
        self.setLayout( layout1 )
        self.update_frustum()

    def stream( self ):
        if not self.streamer.isStreaming():
            self.stream_btn.setStyleSheet( 'background-color: grey;' )
            self.stop_btn.setStyleSheet( 'background-color: red;' )
            self.viewfinder.setStyleSheet( 'background-color: cyan; border:1px hidden red; background:transparent; ' )
            self.update_frustum()
            self.streamer.stream()

    def stop( self ):
        if self.streamer.isStreaming():
            self.stream_btn.setStyleSheet( 'background-color: orange;')
            self.stop_btn.setStyleSheet( 'background-color: white;')
            self.viewfinder.setStyleSheet( 'background-color: cyan; border:5px solid orange; background:transparent; padding:0;' )
            self.streamer.stop()

    def comboChanged( self, text ):
        self.stop()
        self.device = '/dev/{0}'.format( text )

    def resolutionChanged( self, text ):
        self.stop()
        
        if text == 'Elastic':
            min_w = 0
            min_h = 0
            win_w = self.viewfinder.width()
            win_h = self.viewfinder.height()
            
        else:
            res = text.split( 'x' )
            self.res_w = int( res[0] )
            self.res_h = int( res[1] )
            min_w = self.res_w
            min_h = self.res_h
            win_w = self.res_w
            win_h = self.res_h
            
        self.viewfinder.setMinimumWidth( min_w )
        self.viewfinder.setMinimumHeight( min_h )
        self.viewfinder.setGeometry( QRect( self.frame.pos().x(), 0, win_w, win_h ) )
        self.setGeometry( QRect( self.pos().x(), self.pos().y(), win_w, win_h ) )
        self.adjustSize()

    def debug_frustum( self ):
        print( 'Window: {0}, {1}x{2}'.format( self.pos(), self.width(), self.height() ) )
        print( 'Status: {0}'.format( self.title_bar_h ) )
        print( 'Scope:  {0}, {1}x{2}'.format( self.viewfinder.pos(),self.viewfinder.width(), self.viewfinder.height() ) )
        print( 'Device: {0}'.format( self.device ) )

    def update_frustum( self ):
        #self.debug_frustum()
        self.streamer.x = self.pos().x() + self.viewfinder.pos().x() + 0
        self.streamer.y = self.pos().y() + self.viewfinder.pos().y() + self.title_bar_h + 5
        self.streamer.width  = self.viewfinder.width()
        self.streamer.height = self.viewfinder.height()
        self.streamer.device = self.device

    def moveEvent( self, event ):
        self.stop()
        self.update_frustum()
        super().moveEvent(event)

    def resizeEvent(self, event = None):
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
        self._running = True

    def stop( self ):
        self._running = False

    def exit( self ):
        print( 'Exiting' )
        self._running = False
        self._exit = True

    def long_running( self ):
        while not self._exit:
            if self._running:
                print( 'Attempting to start stream' )
                #self.debug_parameters()
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
