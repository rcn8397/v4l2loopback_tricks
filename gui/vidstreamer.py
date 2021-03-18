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

cached_path = lambda media : os.path.join( cache, os.path.basename( media ) )

class FileDialog(QWidget):
    '''FileDialog '''
    def __init__(self, dialog_type = 'Open', title = 'File Dialog'):
        super().__init__()
        self.title  = title
        self.left   = 0
        self.top    = 0
        self.width  = 640
        self.height = 480
        self._type  = dialog_type
        self._paths = []
        self.initUI()
    
    def initUI(self):
        self.setWindowTitle(self.title)
        self.setGeometry(self.left, self.top, self.width, self.height)

        try:
            dialog = { 'Open' : self.openFileNameDialog,
                       'Opens': self.openFileNamesDialog,
                       'Opend': self.openDirNameDialog,
                       'Save' : self.saveFileDialog } [ self._type ]
        except KeyError as e:
            print( str( e ) )

        dialog()
        
        self.show()

    def openDirNameDialog( self ):
        options = QFileDialog.Options()
        options |= QFileDialog.DontUseNativeDialog
        options |= QFileDialog.ShowDirsOnly
        dirName = QFileDialog.getExistingDirectory( self,
                                                    'Select Directory',
                                                    options=options )
        self._paths = []
        if dirName:
            self._paths.append( dirName )
        
    def openFileNameDialog(self):
        options = QFileDialog.Options()
        options |= QFileDialog.DontUseNativeDialog
        fileName, _ = QFileDialog.getOpenFileName(self,"Open File", "","All Files (*);;Python Files (*.py)", options=options)
        self._paths = []
        if fileName:
            self._paths.append( fileName )
    
    def openFileNamesDialog(self):
        options = QFileDialog.Options()
        options |= QFileDialog.DontUseNativeDialog
        files, _ = QFileDialog.getOpenFileNames(self,"Open Files", "","All Files (*);;Python Files (*.py)", options=options)
        self._paths = []
        if files:
            self._paths = files
    
    def saveFileDialog(self):
        options = QFileDialog.Options()
        options |= QFileDialog.DontUseNativeDialog
        fileName, _ = QFileDialog.getSaveFileName(self,"Save File","","All Files (*);;Text Files (*.txt)", options=options)
        self._paths = []
        if fileName:
            self._paths.append( fileName )

    @property
    def path( self ):
        p = None
        try:
            p = self._paths[0]
        except Exception as e:
            pass
        return p

    @path.setter
    def path( self, p ):
        self._paths = []
        self._paths.append( p )
    
    @property
    def paths( self ):
        return self._paths

    @paths.setter
    def paths( self, l ):
        self._paths = l


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
        self.__icons         = None

        # Threading: Streamer (Presentation Thread)
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
        layout = QHBoxLayout()
        menubar = QMenuBar( self )

        # File menu
        filemenu = QMenu( '&File', self )
        menubar.addMenu( filemenu )

        # Delete this
        test_it = lambda x : self.log.append( str( x ) )

        # Open folder
        foldAct = QAction( QIcon(),'&Open Folder', self )
        foldAct.setStatusTip( 'Open Folder' )
        foldAct.triggered.connect( lambda : test_it( 'folder' ) )
        filemenu.addAction( foldAct )

        # Add media
        addAct = QAction( QIcon(), '&Add media', self )
        addAct.setStatusTip( 'Add media to playlist' )
        addAct.triggered.connect( self.add )
        filemenu.addAction( addAct )

        # Remove media
        rmAct = QAction( QIcon(), '&Remove media', self )
        rmAct.setStatusTip( 'Remove media from playlist' )
        rmAct.triggered.connect( self.remove )
        filemenu.addAction( rmAct )

        # Exit app
        exitAct = QAction( QIcon(),'&Exit', self, )
        exitAct.setStatusTip( 'Exit Application' )
        exitAct.triggered.connect( self.exit )
        filemenu.addAction( exitAct )

        # Edit menu
        editmenu = menubar.addMenu( '&Edit' )

        # Video Devices
        devmenu  = editmenu.addMenu( '&Device' )

        self.devgroup = QActionGroup( devmenu )
        self.devgroup.setExclusive( True )
        self.devgroup.triggered.connect( self.editDevice )
        for i, device in enumerate( self.devices ):
            act = QAction( device, self, checkable = True )
            location = '/dev/{0}'.format( device )
            act.setStatusTip( location )
            if device == 'video20':
                act.setChecked( True )
                self.device = '/dev/{0}'.format( device )
            self.devgroup.addAction( act )
            devmenu.addAction( act )

        createAct = QAction( QIcon(), '&Create Icons', self )
        createAct.setStatusTip( 'Create Icons' )
        createAct.triggered.connect( self.create_icons )
        editmenu.addAction( createAct )
        
        # Help menu
        helpmenu = menubar.addMenu( '&Help' )

        layout.addWidget( menubar )
        return( layout )
    
    def init_layout( self ):
        layout_main = QVBoxLayout()
        layout_sxs  = QHBoxLayout()
        layout_list = QVBoxLayout()
        layout_lbtn = QHBoxLayout()
        layout_ctrl = QHBoxLayout()
        layout_mntr = QVBoxLayout()

        # Menu Bar
        layout_menu = self.init_menu()

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
        self.frame.setLayout( layout_ctrl )

        # Play list
        self.find_btn    = QPushButton( self, objectName='find_btn' )
        self.find_btn.setText( 'O' )
        self.find_btn.clicked.connect( self.find )

        self.add_btn = QPushButton( self, objectName='add_btn' )
        self.add_btn.setText( '+' )
        self.add_btn.clicked.connect( self.add )

        self.rm_btn = QPushButton( self, objectName='remove_btn' )
        self.rm_btn.setText( '-' )
        self.rm_btn.clicked.connect( self.remove )

        hspacer = QSpacerItem( self.rm_btn.pos().x() + 10, self.rm_btn.pos().y(), QSizePolicy.Expanding, QSizePolicy.Minimum )

        layout_lbtn.addWidget( self.find_btn )
        layout_lbtn.addWidget( self.add_btn )
        layout_lbtn.addWidget( self.rm_btn )
        layout_lbtn.addItem( hspacer )
        layout_lbtn.setContentsMargins( 0,0,0,0)

        self.progressBar = QProgressBar( self )
        self.progressBar.setValue(0)

        self.playlist   = QListView( self )
        self.mediafiles = QStandardItemModel()
        self.playlist.setModel( self.mediafiles )
        self.playlist.clicked.connect( self.selectionChanged )

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


    def build_playlist( self ):
        ''' Build the playlist '''
        self.log.append( 'Building playlist' )
        self.mediafiles.clear()

        for path in sources:
            icon = os.path.join( cached_path( path ), 'icon.jpg' )
            if not os.path.exists( icon ):
                icon = ''
            self.new_playlist_item( path, icon )

    def new_playlist_item( self, s, icon = '' ):
        item = QStandardItem( QIcon( icon ), os.path.basename( s ) )
        self.mediafiles.appendRow( item )

    def add( self ):
        self.log.append('Adding: ' )
        add = FileDialog('Opens')

        self.log.append( '{}'.format( add.paths ) )
        if len( add.paths ) == 0:
            return # Bail early

        sources.extend( add.paths )        
        self.build_playlist()

        # This will cause the playlist to flash
        self.create_icons()
        
        # Default to the item just added
        rows  = self.mediafiles.rowCount()
        item  = self.mediafiles.index( rows-1, 0 )
        model = self.playlist.selectionModel()
        model.select( item, QItemSelectionModel.Select)

        # Update the selected media
        self.selected_media = sources[ rows- 1 ] #item.data()
        self.log.append( 'Queued: {}'.format( self.selected_media ) )

        # Create a preview of the item selected.
        self.create_preview()

    def remove( self ):
        self.log.append( 'remove' )


    def create_icons( self ):
        self.__icons = []
        thread = QThread()
        thread.setObjectName( 'Icon' )
        worker = IconSource( 0 )

        # Keep references to workers and threads to avoid GC
        self.__icons.append( (thread, worker ) )
        worker.moveToThread( thread )

        # Connect signals
        worker.sig_step.connect( self.icon_step )
        worker.sig_done.connect( self.icon_done )
        worker.sig_msg.connect( self.log.append )
        self.sig_abort_workers.connect( worker.abort )

        thread.started.connect( worker.create )
        thread.start()
        self.log.append( 'Icon thread started' )

    @pyqtSlot( int )
    def icon_step( self, data: int ):
        self.progressBar.setValue( data ) # remove me later

    @pyqtSlot( int )
    def icon_done( self, worker_id ):
        self.log.append( 'Icon worker #{} finsihed'.format(worker_id) )

        # Update preview
        self.log.append( 'Updating Icons' )                
        self.build_playlist()
        
        # Clean up the thread
        for thread, work in self.__icons:
            thread.quit()
            thread.wait()
        self.log.append( 'All icons exited' )      
        

    def create_preview( self, path = None ):
        self.log.append( 'preview' )

        self.__previews = []
        thread = QThread()
        thread.setObjectName( 'Preview' )

        if path is None:
            worker = PreviewSource( 0, self.selected_media )
        else:
            worker = PreviewSource( 0, path )

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

        # Update preview       
        outdir  = cached_path( self.selected_media )
        gif     = '{}.gif'.format( os.path.basename( self.selected_media ) )
        preview = os.path.join( outdir, gif )
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
        folder = FileDialog('Opend')
        self.log.append( '{}'.format( folder.path ) )
        
        if folder.path is None:
            return # Bail early
        else:
            self.dirname = folder.path

        self.progressBar.setValue( 0 )
        self.log.append( 'Sources: {0}'.format( sources ) )
        self.find_btn.setDisabled( True )
        self.add_btn.setDisabled( True )
        self.rm_btn.setDisabled( True )

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
        self.add_btn.setEnabled( True )
        self.rm_btn.setEnabled( True )

        # Update the list view
        # This will cause the playlist to flash
        self.build_playlist()        
#        self.log.append( 'Updating sources' )
#        self.mediafiles.clear()
#        for i, path in enumerate( sources ):
#            self.new_playlist_item( path )
            
        # Default to the zeroth item
        item = self.mediafiles.index( 0, 0 )
        model = self.playlist.selectionModel()
        model.select( item, QItemSelectionModel.Select)

        # Update the selected media
        self.selected_media = sources[ 0 ]
        self.log.append( 'Queued: {}'.format( self.selected_media ) )

        # Create a preview of the item selected.
        self.create_preview()

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

    def editDevice( self, action ):
        text = action.text()
        self.stop()
        self.device = '/dev/{0}'.format( text )
        self.streamer.device = self.device
        self.log.append( 'Changed video device: {}'.format( text ) )
        
    def selectionChanged( self, index ):
        self.log.append( 'selected: {}'.format( index.row() ) )
        self.log.append( 'Queued: {}'.format( sources[ index.row()] ) )
        self.selected_media = sources[ index.row()]
        self.create_preview()

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
    sig_done = pyqtSignal(int)  # Id, end of job
    sig_msg  = pyqtSignal(str)  # msg to user

    def __init__( self, id:int, path:str ):
        super( PreviewSource, self ).__init__()
        self.__id    = id
        self.__abort = False
        self.__path  = path

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

        outdir = os.path.join( cache, os.path.basename( self.__path ) )
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
        basename = os.path.basename( self.__path )
        gif = '{}.gif'.format( basename )
        outfile = os.path.join( outdir, gif )
        pattern = os.path.join( outdir, 'preview_%03d.jpg' )

        self.sig_msg.emit( 'Pattern: {}'.format( pattern ) )
        self.sig_msg.emit( 'Generating preview: {} from {}'.format( outfile, pattern ) )
        jpgs2gif( pattern, out = outfile )

        self.sig_done.emit( self.__id )

    def abort( self ):
        msg = 'Preview #{} notified to abort'.format(self.__id)
        self.sig_msg.emit( msg )
        self.__abort = True


class IconSource( QObject ):
    sig_step = pyqtSignal(int)  # Id, step description
    sig_done = pyqtSignal(int)  # Id, end of job
    sig_msg  = pyqtSignal(str)  # msg to user

    def __init__( self, id:int ):
        super( IconSource, self ).__init__()
        self.__id    = id
        self.__abort = False
        self.__root  = cache

    @pyqtSlot()
    def create( self ):
        ''' Perform task '''
        thread_name = QThread.currentThread().objectName()
        thread_id   = int( QThread.currentThreadId() )

        self.sig_msg.emit('Attempting to generation icon thumbnails')
        for i, path in enumerate( sources ):
            self.sig_msg.emit('Iconify: {}'.format( path ) )
            duration = probe_duration( path )
            outdir = os.path.join( self.__root, os.path.basename( path ) )
            if not os.path.exists( outdir ):
                fsutil.mkdir_p( outdir )

            # Make a thumbnail icon if it doesn't already exist
            outfile= 'icon.jpg'
            outpath = os.path.join( outdir, outfile )

            if not os.path.exists( outpath ):
                ts = duration * 0.10
                self.sig_msg.emit( 'Generating icon: {} @ {} seconds'.format( outpath, ts ) )
                generate_thumbnail( path, outpath, time = ts )           
            self.sig_step.emit( i )
    
            # Check for abort
            if self.__abort:
                self.sig_msg.emit('Aborting')
                break

        self.sig_msg.emit( 'done' )
        self.sig_done.emit( self.__id )

    def abort( self ):
        msg = 'Icon #{} notified to abort'.format(self.__id)
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
