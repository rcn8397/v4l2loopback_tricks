#!/usr/bin/env python3
import os
import sys
import time
from PyQt5.QtCore    import QTimer, Qt, QEvent, pyqtSignal, QThread, QObject, QRect, QSize
from PyQt5.QtWidgets import QApplication, QMainWindow, QListView, QFileSystemModel, QTreeView
from PyQt5.QtWidgets import QLabel, QGridLayout, QPushButton, QWidget, QComboBox, QScrollArea
from PyQt5.QtWidgets import QHBoxLayout, QVBoxLayout, QStyle, QFrame


# Setup imports from module
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from v4l2tricks.ffmpeg_if import DesktopScopeProcess

get_video_devices = lambda : [ dev for dev in os.listdir('/dev') if 'video' in dev ]

class VidStreamer( QWidget ):
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

        #self.setWindowFlags( self.windowFlags() )

        # Show the window
        self.show()


    def init_layout( self ):
        layout_main = QVBoxLayout()
        layout_sxs  = QHBoxLayout()
        layout_list = QVBoxLayout()
        layout_ctrl = QHBoxLayout()
        layout_mntr = QVBoxLayout()

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
        background-color: white;
        }
        QFrame{
        background-color: #3E3E3E;
        border-radius: 10px;
        }
        '''
        self.frame.setStyleSheet( style )

        layout_ctrl.addWidget( self.stream_btn )
        layout_ctrl.addWidget( self.stop_btn )
        layout_ctrl.addWidget( resolution )
        layout_ctrl.addWidget( combo )
        self.frame.setLayout( layout_ctrl )

        self.treeview = QTreeView()
        self.mediafiles = QFileSystemModel(self.treeview, objectName='media_files')
        self.mediafiles.setReadOnly( True )

        path = self.mediafiles.setRootPath( '.' )
        self.treeview.setModel( self.mediafiles )
        self.treeview.setRootIndex( path )

        layout_list.addWidget( self.treeview )

        self.nowplaying = QLabel( self, objectName='now_playing' )
        self.nextup     = QLabel( self, objectName='next_up' )
        style='''
        QLabel{
        background-color: orange;
        }
        QLabel#now_playing{
        border:5px solid cyan;
        }
        QLabel#next_up{
        border:5px solid blue;
        }

        '''
        self.nowplaying.setStyleSheet( style )
        self.nowplaying.setGeometry( QRect( self.frame.pos().x(), 0, 640, 480 ) )
        self.nowplaying.setFixedHeight( 240 )
        self.nowplaying.setFixedWidth( 360 )

        layout_mntr.addWidget( self.nowplaying )
        #layout_mntr.addWidget( self.nextup )

        # Add layouts to main layout
        layout_sxs.addLayout( layout_list )
        layout_sxs.addLayout( layout_mntr )

        layout_main.addLayout( layout_sxs )
        layout_main.addWidget( self.frame )


        #self.setAttribute( Qt.WA_TranslucentBackground )
        self.setLayout( layout_main )
        self.update_frustum()

    def stream( self ):
        if not self.streamer.isStreaming():
            self.stream_btn.setStyleSheet( 'background-color: grey;' )
            self.stop_btn.setStyleSheet( 'background-color: red;' )
            self.streamer.stream()

    def stop( self ):
        if self.streamer.isStreaming():
            self.stream_btn.setStyleSheet( 'background-color: orange;')
            self.stop_btn.setStyleSheet( 'background-color: white;')
            self.streamer.stop()

    def comboChanged( self, text ):
        self.stop()
        self.device = '/dev/{0}'.format( text )

    def resolutionChanged( self, text ):
        self.stop()
        res = text.split( 'x' )
        self.res_w = int( res[0] )
        self.res_h = int( res[1] )

    def debug_frustum( self ):
        print( 'Window: {0}, {1}x{2}'.format( self.pos(), self.width(), self.height() ) )
        print( 'Status: {0}'.format( self.title_bar_h ) )
        print( 'Device: {0}'.format( self.device ) )

    def update_frustum( self ):
        self.debug_frustum()
        self.streamer.device = self.device

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
    ss = VidStreamer()
    sys.exit( app.exec_() )

# Standard biolerplate to call the main() function to begin the program
if __name__ == '__main__':
    main()
