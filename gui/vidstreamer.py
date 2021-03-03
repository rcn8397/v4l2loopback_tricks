#!/usr/bin/env python3
import os
import sys
import time
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *

# Setup imports from module
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from v4l2tricks.stream import stream_media
from v4l2tricks.supported import MediaContainers
from v4l2tricks           import fsutil

get_video_devices = lambda : [ dev for dev in os.listdir('/dev') if 'video' in dev ]

# Media extensions
containers  = MediaContainers()
media_types = containers.extensions()

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
        #self.setGeometry( 0, 0, 640, 500 )

        self.init_layout()

        #self.setWindowFlags( self.windowFlags() )

        # Show the window
        self.show()


    def init_layout( self ):
        layout_main = QVBoxLayout()
        layout_sxs  = QHBoxLayout()
        layout_list = QVBoxLayout()
        layout_lbtn = QHBoxLayout()
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

        # Play list
        self.find_btn    = QPushButton( self, objectName='find_btn' )
        self.find_btn.setText( 'O' )
        self.find_btn.clicked.connect( self.find )

        add_btn = QPushButton( self, objectName='add_btn' )
        add_btn.setText( '+' )
        add_btn.clicked.connect( self.add )

        rm_btn = QPushButton( self, objectName='remove_btn' )
        rm_btn.setText( '-' )
        rm_btn.clicked.connect( self.remove )
        layout_lbtn.addWidget( self.find_btn )
        layout_lbtn.addWidget( add_btn )
        layout_lbtn.addWidget( rm_btn )
        layout_lbtn.setContentsMargins( 0,0,0,0)
        
        self.playlist   = QListView( self )
        self.mediafiles = QStandardItemModel()
        self.playlist.setModel( self.mediafiles )
        self.load_sources()
        
        layout_list.addWidget( self.playlist )
        layout_list.addLayout( layout_lbtn )

        self.nowplaying = QLabel( self, objectName='now_playing' )
        style='''
        QLabel{
        background-color: orange;
        }
        QLabel#now_playing{
        border:5px solid cyan;
        }
        '''
        self.nowplaying.setStyleSheet( style )
        self.nowplaying.setGeometry( QRect( self.frame.pos().x(), 0, 640, 480 ) )
        self.nowplaying.setFixedHeight( 240 )
        self.nowplaying.setFixedWidth( 360 )

        layout_mntr.addWidget( self.nowplaying )

        # Add layouts to main layout
        layout_sxs.addLayout( layout_list )
        layout_sxs.addLayout( layout_mntr )

        layout_main.addLayout( layout_sxs )
        layout_main.addWidget( self.frame )


        #self.setAttribute( Qt.WA_TranslucentBackground )
        self.setLayout( layout_main )

    def init_src_updater(self):
        self.src_thread = QThread()
        self.src_worker = SourceUpdater()
        self.src_worker.moveToThread( self. src_thread )

        # Connect signals and slots
        self.src_thread.started.connect(self.src_worker.run)
        self.src_worker.finished.connect(self.src_thread.quit)
        self.src_worker.finished.connect(self.src_worker.deleteLater)
        self.src_thread.finished.connect(self.src_thread.deleteLater)
        self.src_worker.progress.connect(self.reportProgress )

        # Start the thread
        self.src_thread.start()

        # Final
        self.find_btn.setEnabled(False)
        self.src_thread.finished.connect(
            lambda: self.find_btn.setEnabled( True )
        )
        self.src_thread.finished.connect(
            self.update_sources
        )
        
    def add( self ):
        print( 'add' )

    def remove( self ):
        print( 'remove' )
        
    def find( self ):
        self.load_sources()

    def update_sources(self):
        self.mediafiles.clear()
        icon = 'icons/export/32x32/cog.png'
        for i, path in enumerate( self.sources ):
            print( os.path.basename( path ) )
            item = QStandardItem( path )
            self.mediafiles.appendRow( item )
            item.setData( QIcon( icon ), Qt.DecorationRole )
        print( 'done' )

    def load_sources( self, dirname = '.' ):
        self.sources = fsutil.find( dirname, media_types )
        self.update_sources()

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


class SourceUpdater( QObject ):
    finished = pyqtSignal()
    progress = pyqtSignal()
    def __init__( self ):
        super( SourceUpdater, self ).__init__()
        self._running = False
        self._exit    = False

    def discover( self ):
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
                print( 'Running Source Updater' )
                time.sleep(1)
                #self.sources = fsutil.find( dirname, media_types )
        self.finished.emit()
        print( '{0} finished'.format( __class__.__name__ ) )
        
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
