#!/usr/bin/env python3
import os
import sys
import time
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *

# Setup imports from module
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from v4l2tricks.stream    import stream_media
from v4l2tricks.ffmpeg_if import generate_thumbnail, jpgs2gif, probe_duration
from v4l2tricks.supported import MediaContainers
from v4l2tricks           import fsutil

def trap_exc_during_debug(*args):
    # when app raises uncaught exception, print info
    print(args)


# install exception hook: without this, uncaught exception would cause application to exit
#sys.excepthook = trap_exc_during_debug

get_video_devices = lambda : [ dev for dev in os.listdir('/dev') if 'video' in dev ]

# Media extensions
containers  = MediaContainers()
media_types = containers.extensions()

cache   = os.path.expanduser( '~/.v4l2tricks' )
sources = list()
mutex   = QMutex()

class VidStreamer( QWidget ):
    resize_signal  = pyqtSignal(int)
    sig_abort_workers = pyqtSignal()

    def __init__( self ):
        super().__init__()
        self.title_bar_h   = self.style().pixelMetric( QStyle.PM_TitleBarHeight )
        self.dirname       = '.'
        self.src_threads   = []
        self.devices       = get_video_devices()
        self.device        = '/dev/{0}'.format( self.devices[0] )

        self.selected_media = None

        # Threading: Media updaters
        self.__updaters      = None
        self.__previews      = None

        # Threading: Streamer
        self.stream_thread = QThread(parent=self)
        self.streamer      = MediaStreamer()
        self.streamer.moveToThread( self.stream_thread )
        self.streamer.finished.connect( self.stream_thread.quit )
        self.streamer.finished.connect( self.streamer.deleteLater )
        self.stream_thread.finished.connect( self.stream_thread.deleteLater )
        self.stream_thread.start()
        self.stream_thread.started.connect( self.streamer.long_running )

        self.setWindowTitle( self.__class__.__name__ )

        self.init_layout()
        self.init_cache()

        # Show the window
        self.show()


    def init_cache( self ):
        if not os.path.exists( cache ):
            self.log.append( 'Creating {} cache {}'.format( self.__class__.__name__, cache ) )
            fsutil.mkdir_p( cache )

    def init_menu( self ):
        menubar = QMenuBar( self )
        
        # Creating menu items
        filemenu = QMenu( '&File', self )
        menubar.addMenu( filemenu )
        
        editmenu = menubar.addMenu( '&Edit' )
        helpmenu = menubar.addMenu( '&Help' )

    def init_layout( self ):
        layout_main = QVBoxLayout()
        layout_menu = QHBoxLayout()
        layout_sxs  = QHBoxLayout()
        layout_list = QVBoxLayout()
        layout_lbtn = QHBoxLayout()
        layout_ctrl = QHBoxLayout()
        layout_mntr = QVBoxLayout()


        # Menu Bar
        menubar = QMenuBar( self )
        filemenu = QMenu( '&File', self )
        menubar.addMenu( filemenu )
        exitAct = QAction( QIcon(),'&Exit', self, )
        exitAct.setStatusTip( 'Exit Application' )
        exitAct.triggered.connect( self.exit )
        filemenu.addAction( exitAct )
        
        
        editmenu = menubar.addMenu( '&Edit' )
        helpmenu = menubar.addMenu( '&Help' )
        layout_menu.addWidget( menubar )

        # Get video devices
        combo      = QComboBox( self )
        for i, device in enumerate( self.devices ):
            combo.addItem( device )
            if device == 'video20':
               combo.setCurrentIndex( i )
               self.device = '/dev/{0}'.format( device )
        combo.activated[str].connect( self.comboChanged )

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

        hspacer = QSpacerItem( rm_btn.pos().x() + 10, rm_btn.pos().y(), QSizePolicy.Expanding, QSizePolicy.Minimum )

        self.prev_btn = QPushButton( self, objectName='prev_btn' )
        self.prev_btn.setText( 'p' )
        self.prev_btn.clicked.connect( self.preview )
        self.prev_btn.setDisabled( True )

        layout_lbtn.addWidget( self.find_btn )
        layout_lbtn.addWidget( add_btn )
        layout_lbtn.addWidget( rm_btn )
        layout_lbtn.addItem( hspacer )
        layout_lbtn.addWidget( self.prev_btn )
        layout_lbtn.setContentsMargins( 0,0,0,0)

        self.progressBar = QProgressBar( self )
        #self.progressBar.setGeometry(QtCore.QRect(10, 260, 381, 23))
        self.progressBar.setValue(0)

        self.playlist   = QListView( self )
        self.mediafiles = QStandardItemModel()
        self.playlist.setModel( self.mediafiles )
        self.playlist.clicked.connect( self.selectionChanged )

        directories = QComboBox( self )
        home = os.path.expanduser( '~/' )
        directories.addItem( '.' )
        directories.addItem( home )
        for f in os.listdir( home ):
            abs_path = os.path.join( home, f )
            if os.path.isdir( abs_path ):
                directories.addItem( abs_path  )
        directories.activated[str].connect( self.directoryChanged )
        layout_list.addWidget( directories )
        layout_list.addWidget( self.playlist )
        layout_list.addLayout( layout_lbtn )
        layout_list.addWidget( self.progressBar )

        self.nowplaying = QLabel( self, objectName='now_playing' )
        self.preview    = QLabel( self, objectName='preview' )
        style='''
        QLabel{
        background-color: black;
        }
        QLabel#now_playing{
        border:5px solid cyan;
        }
        QLabel#preview{
        border:5px solid green;
        }
        '''
        self.nowplaying.setStyleSheet( style )
        self.nowplaying.setFixedHeight( 240 )
        self.nowplaying.setFixedWidth( 360 )

        self.preview.setStyleSheet( style )
        self.preview.setFixedHeight( 240 )
        self.preview.setFixedWidth( 360 )

        layout_mntr.addWidget( self.nowplaying )
        layout_mntr.addWidget( self.preview )

        # Log output
        self.log = QTextEdit()

        # Add layouts to main layout
        layout_sxs.addLayout( layout_list )
        layout_sxs.addLayout( layout_mntr )
        layout_main.addLayout( layout_menu )
        layout_main.addLayout( layout_sxs )
        layout_main.addWidget( self.frame )
        layout_main.addWidget( self.log )
        self.setLayout( layout_main )

    def add( self ):
        self.log.append('add' )

    def remove( self ):
        self.log.append( 'remove' )

    def preview( self ):
        self.log.append( 'preview' )
        self.prev_btn.setDisabled( True )

        self.__previews = []
        thread = QThread()
        thread.setObjectName( 'Preview' )
        worker = PreviewSource( 0, self.selected_media )

        # Keep references to workers and threads to avoid GC
        self.__previews.append( (thread, worker ) )
        worker.moveToThread( thread )

        # Connect signals
        worker.sig_step.connect( self.preview_step )
        worker.sig_done.connect( self.preview_done )
        worker.sig_msg.connect( self.log.append )
        self.sig_abort_workers.connect( worker.abort )

        thread.started.connect( worker.preview )
        thread.start()
        self.log.append( 'Preview thread started' )

    @pyqtSlot( int )
    def preview_step( self, data: int ):
        self.progressBar.setValue( data ) # remove me later

    @pyqtSlot( int )
    def preview_done( self, worker_id ):
        self.log.append( 'Preview worker #{} finsihed'.format(worker_id) )
        self.prev_btn.setEnabled( True )

        # Update preview
        outdir  = os.path.join( cache, os.path.basename( self.selected_media ) )
        preview = os.path.join( outdir, '{}.gif'.format( self.selected_media ) )
        self.log.append( 'Looking for preview: {}, {}'.format( preview, os.path.exists( preview ) ) )
        movie = QMovie( preview )
        self.preview.setMovie( movie )
        movie.start()

        # Clean up the thread
        for thread, work in self.__previews:
            thread.quit()
            thread.wait()
        self.log.append( 'All previews exited' )


    def find( self ):
        self.progressBar.setValue( 0 )
        self.log.append( 'Sources: {0}'.format( sources ) )
        self.find_btn.setDisabled( True )

        self.__updaters = []
        thread = QThread()
        thread.setObjectName( 'Updater' )
        worker = SourceUpdater( 0, self.dirname )
        # Keep references to worker and thread to avoid garbage collection
        self.__updaters.append( ( thread, worker ) )
        worker.moveToThread( thread )

        # Connect signals
        worker.sig_step.connect( self.discover_step )
        worker.sig_done.connect( self.discover_done )
        worker.sig_msg.connect(  self.log.append )
        self.sig_abort_workers.connect( worker.abort )

        thread.started.connect( worker.discover )
        thread.start()
        self.log.append( 'Thread started' )

    @pyqtSlot( int, int )
    def discover_step( self, worker_id: int, data: int ):
        self.progressBar.setValue( data )

    @pyqtSlot( int )
    def discover_done( self, worker_id ):
        self.log.append( 'worker #{} finsihed'.format(worker_id) )
        self.progressBar.setValue( 100 )
        self.find_btn.setEnabled( True )

        # Update the list view
        self.log.append( 'Updating sources' )
        self.mediafiles.clear()
        for i, path in enumerate( sources ):
            item = QStandardItem( path )
            self.mediafiles.appendRow( item )

        # Default to the zeroth item
        item = self.mediafiles.index( 0, 0 )
        model = self.playlist.selectionModel()
        model.select( item, QItemSelectionModel.Select)
        self.selected_media = item.data()
        self.log.append( 'Queued: {}'.format( self.selected_media ) )
        self.prev_btn.setEnabled( True )

        # Clean up the thread
        for thread, work in self.__updaters:
            thread.quit()
            thread.wait()
        self.log.append( 'All updaters exited' )

    @pyqtSlot()
    def abort_discover( self ):
        self.sig_abort_workers.emit()
        self.log.append( 'Requesting abort' )
        for thread, work in self.__updaters:
            thread.quit()
            thread.wait()
        self.log.append( 'All updaters exited' )

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

    def selectionChanged( self, index ):
        self.log.append( 'Queued: {}'.format(index.data()))
        self.selected_media = index.data()

    def directoryChanged( self, text ):
        self.dirname = text

    def comboChanged( self, text ):
        self.stop()
        self.device = '/dev/{0}'.format( text )
        self.streamer.device = self.device

    def closeEvent( self, event ):
        self.thread_clean_up()
        super().closeEvent( event )

    def exit( self ):
        self.thread_clean_up()
        qApp.quit()

    def thread_clean_up( self ):
        print( 'Cleaning up thread' )
        self.streamer.exit()
        self.stream_thread.quit()
        self.stream_thread.wait()

class PreviewSource( QObject ):
    sig_step = pyqtSignal(int)  # Id, step description
    sig_done = pyqtSignal(int)      # Id, end of job
    sig_msg  = pyqtSignal(str)      # msg to user

    def __init__( self, id:int, path:str ):
        super( PreviewSource, self ).__init__()
        self.__id    = id
        self.__abort = False
        self.__path  = path
        self.__root  = cache

    @pyqtSlot()
    def preview( self ):
        ''' Perform task '''
        thread_name = QThread.currentThread().objectName()
        thread_id   = int( QThread.currentThreadId() )

        self.sig_msg.emit('Attempting to generation preview thumbnails')
        self.sig_msg.emit('Media Selected: {}'.format( self.__path ) )

        duration = probe_duration( self.__path )
        self.sig_msg.emit( 'duration: {}'.format( duration ) )

        increments = 4
        timestamp = lambda duration, step: ( ( duration/step ) - ( 0.5 * ( duration * 1.0/increments ) ) )

        outdir = os.path.join( self.__root, os.path.basename( self.__path ) )
        if not os.path.exists( outdir ):
            fsutil.mkdir_p( outdir )

        # Make 4 thumbnails for previewing
        for i in range( increments, 0, -1 ):
            step = (increments + 1) - i
            ts = timestamp( duration, step )

            outfile= '{}_{:03}.jpg'.format( 'preview', i )
            outpath = os.path.join( outdir, outfile )
            self.sig_msg.emit( 'Generating preview {}: {} @ {} seconds'.format( step, outpath, ts ) )
            generate_thumbnail( self.__path, outpath, time = ts )
            self.sig_step.emit( i )

            # Check for abort
            if self.__abort:
                self.sig_msg.emit('Aborting')
                break

        # Generate a gif from the previews
        preview = os.path.join( outdir, '{}.gif'.format( self.__path ) )
        pattern = os.path.join( outdir, 'preview_%03d.jpg' )
        self.sig_msg.emit( 'Generating preview: {} from {}'.format( preview, pattern ) )
        jpgs2gif( pattern, out = preview )

        self.sig_done.emit( self.__id )

    def abort( self ):
        msg = 'Preview #{} notified to abort'.format(self.__id)
        self.sig_msg.emit( msg )
        self.__abort = True

class SourceUpdater( QObject ):
    sig_step = pyqtSignal(int,int) # Id, step description
    sig_done = pyqtSignal(int)      # Id, end of job
    sig_msg  = pyqtSignal(str)      # msg to user

    def __init__( self, id:int, path:str, excludes = ['.git', '.svn'] ):
        super( SourceUpdater, self ).__init__()
        self.__id = id
        self.__abort = False
        self.__path  = path
        self.__excludes = excludes

    @pyqtSlot()
    def discover( self ):
        ''' Perform task '''
        thread_name = QThread.currentThread().objectName()
        thread_id   = int( QThread.currentThreadId() )
        msg = 'Running worker #{} from thread "{}" (#{})'.format(self.__id, thread_name, thread_id)
        self.sig_msg.emit(msg)

        is_xcl = lambda x, xcl : any( e in x for e in xcl )
        is_ext = lambda f, ext : any( f.endswith( e ) for e in ext )

        self.sig_msg.emit( 'Clearing sources' )
        sources.clear()

        fcnt = 0
        self.sig_msg.emit( 'Searching...' )
        for root, dirs, files in os.walk( self.__path ):#, topdown=True ):
            files= [ f for f in files if not f.startswith( '.' ) ]
            dirs = [ d for d in dirs  if not d.startswith( '.' ) ]
            if is_xcl( root, self.__excludes ):
                # Skip excluded directories
                #self.sig_msg.emit( 'Skipping: {}'.format( root ) )
                continue

            for fname in files:
                fcnt += 1
                self.sig_msg.emit( 'checking root={}, file={}'.format(root, fname ) )
                self.sig_step.emit( 0, fcnt )
                if is_ext( fname.lower(), media_types ):
                    path = os.path.join( root, fname )
                    sources.append( path )

                # Check for abort
                if self.__abort:
                    self.sig_msg.emit('Aborting')
                    break

        self.sig_done.emit( self.__id )

    def abort( self ):
        msg = 'Worker #{} notified to abort'.format(self.__id)
        self.sig_msg.emit( msg )
        self.__abort = True


class MediaStreamer( QObject ):
    finished = pyqtSignal()

    def __init__( self ):
        super(MediaStreamer, self).__init__()
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
                self.debug_parameters()
                time.sleep(1)
                #self.start_streaming()

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
