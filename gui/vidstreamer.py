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
from gui.wait             import QtWaitSpinner

def trap_exc_during_debug(*args):
    # when app raises uncaught exception, print info
    print(args)

# install exception hook: without this, uncaught exception would cause application to exit
#sys.excepthook = trap_exc_during_debug

get_video_devices = lambda : [ dev for dev in os.listdir('/dev') if 'video' in dev ]

# Media extensions
containers      = MediaContainers()
#media_types     = containers.extensions()
media_types = {'.flv', '.mp4', '.webm', '.mov', '.m4a', '.ogg', '.mkv', '.3gp', '.asf', '.wma', '.mpg', '.divx', '.mpeg', '.wmv', '.vob', '.avi'}
media_types_str = ' '.join( '*{}'.format( t ) for t in media_types )

# Settings
class SettingsManager( object ):
    VIDEO    ='video'
    DISCOVER ='discover'
    DEBUG    ='debug'

    def __init__( self, filename ):
        self.settings = QSettings( filename, QSettings.IniFormat )
        self.defaults()

    def setkey( self, domain, key, value ):
        self.settings.setValue( os.path.join( domain, key ), value )

    def getkey( self, domain, key ):
        return self.settings.getValue( os.path.join( domain, key ) )

    def sync( self ):
        self.settings.sync()

    def defaults( self ):
        self.setkey( self.VIDEO,    'device',       '/dev/video20' )
        self.setkey( self.DEBUG,    'debug',        False )
        self.setkey( self.DEBUG,    'verbose',      False )
        self.setkey( self.VIDEO,    'auto_preview', True )
        self.setkey( self.VIDEO,    'auto_icon',    True )

        # Sync the settings
        self.sync()

    def dump( self ):
        for k in self.settings.allKeys():
            value = self.settings.value( k )
            print( k, value, type( value ) )


icon_path   = 'resources'
cache       = os.path.expanduser( '~/.v4l2tricks' )
cached_path = lambda media : os.path.join( cache, os.path.basename( media ) )
config_path = cached_path( 'vidstreamer.ini' )

#settings    = SettingsManager( config_path )
#settings.dump()

sources = list()

def create_icon( path ):
    ''' Create an icon of the media at <path> '''
    duration = probe_duration( path )
    outdir   = cached_path( path )
    outpath  = os.path.join( outdir, 'icon.jpg' )
    if not os.path.exists( outdir ):
        fsutil.mkdir_p( outdir )

    # Make a thumbnail icon if it doesn't already exist
    if not os.path.exists( outpath ):
        ts = duration * 0.10
        generate_thumbnail( path, outpath, time = ts )

def create_gif( path, increments = 4, overwrite = False ):
    '''
    Generate a gif from media at <path>, from <increments> fragments
    '''
    duration  = probe_duration(path )
    timestamp = lambda duration, step: ( ( duration/step ) - ( 0.5 * ( duration * 1.0/increments ) ) )
    basename  = os.path.basename( path )
    outdir    = os.path.join( cache, basename )
    gif       = '{}.gif'.format( basename )

    if not os.path.exists( outdir ):
        fsutil.mkdir_p( outdir )

    # Make 4 thumbnails for previewing
    for i in range( increments, 0, -1 ):
        step = (increments + 1) - i
        ts = timestamp( duration, step )
        outfile= '{}_{:03}.jpg'.format( 'preview', i )
        outpath = os.path.join( outdir, outfile )
        if not os.path.exists( outpath ) or overwrite:
            generate_thumbnail( path, outpath, time = ts )

    # Generate a gif from the previews if one doesn't already exist
    outfile   = os.path.join( outdir, gif )
    pattern   = os.path.join( outdir, 'preview_%03d.jpg' )                              
    if not os.path.exists( outfile ) or overwrite:
        jpgs2gif( pattern, out = outfile )



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
        self.setFixedSize( self.width, self.height )

        try:
            dialog = { 'Open' : self.openFileNameDialog,
                       'Opens': self.openFileNamesDialog,
                       'Opend': self.openDirNameDialog,
                       'Save' : self.saveFileDialog } [ self._type ]
        except KeyError as e:
            print( str( e ) )

        dialog()

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
        fileName, _ = QFileDialog.getOpenFileName(self,"Open File", "","Media Files ({})".format( media_types_str ), options=options)
        self._paths = []
        if fileName:
            self._paths.append( fileName )

    def openFileNamesDialog(self):
        options = QFileDialog.Options()
        options |= QFileDialog.DontUseNativeDialog
        files, _ = QFileDialog.getOpenFileNames(self,"Open Files", "","Media Files ({})".format( media_types_str ), options=options)
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
        self.log_shown      = True
        self.enable_icons   = True
        self.enable_preview = True
        self.selected_media = None

        # Threading: Media updaters
        self.__updaters      = None

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
        self.setWindowIcon( QIcon( os.path.join( icon_path, 'tophat.svg' ) ) )

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

        # Open folder
        foldAct = QAction( QIcon(),'&Open Folder', self )
        foldAct.setStatusTip( 'Open Folder' )
        foldAct.triggered.connect( self.find )
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

        self.togglelog  = QAction( QIcon(), 'Show &Log', self )
        self.togglelog.setStatusTip( 'Show/Hide log' )
        self.togglelog.triggered.connect( self.toggle_log )
        editmenu.addAction( self.togglelog )

        self.iconact = QAction( QIcon(), 'Disable &Icons', self )
        self.iconact.setStatusTip( 'Disable/Enable Icons' )
        self.iconact.triggered.connect( self.toggle_icons )
        editmenu.addAction( self.iconact )

        self.previewact = QAction( QIcon(), 'Disable &Preview', self )
        self.previewact.setStatusTip( 'Disable/Enable Preview' )
        self.previewact.triggered.connect( self.toggle_preview )
        editmenu.addAction( self.previewact )


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
        #background-color: #3E3E3E;
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

        self.playlist   = QListView( self )
        self.mediafiles = QStandardItemModel()
        self.playlist.setModel( self.mediafiles )
        self.playlist.clicked.connect( self.selectionChanged )

        self.playlist_busy = QtWaitSpinner( self.playlist )
        self.playlist_busy.trailFadePercent = 20
        self.playlist_busy.minTrailOpacity = 50
        self.playlist_busy.setColor( QColor( Qt.black ) )

        layout_list.addWidget( self.playlist )
        layout_list.addLayout( layout_lbtn )

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
        self.playlist_busy.start()
        self.log.append('Adding: ' )
        add = FileDialog('Opens')

        self.log.append( '{}'.format( add.paths ) )
        if len( add.paths ) == 0:
            self.playlist_busy.stop()
            return # Bail early

        sources.extend( add.paths )

        # This could take some time... it might need to be threaded after all
        for path in add.paths:
            create_icon( path )

        self.build_playlist()

        # Default to the item just added
        rows  = self.mediafiles.rowCount()
        item  = self.mediafiles.index( rows-1, 0 )
        model = self.playlist.selectionModel()
        model.select( item, QItemSelectionModel.Select)

        # Update the selected media
        self.selected_media = sources[ rows- 1 ] #item.data()
        self.log.append( 'Queued: {}'.format( self.selected_media ) )
        self.streamer.path = self.selected_media

        # Create a preview of the item selected.
        create_gif( self.selected_media )
        self.update_preview()
        self.playlist_busy.stop()

    def selectRow( self, row ):
        model = self.playlist.selectionModel()
        item  = self.mediafiles.index( row, 0 )
        model.select( item, QItemSelectionModel.Select )
        self.update_preview()

    def remove( self ):
        self.log.append( 'remove' )
        model = self.playlist.model()
        for item in self.playlist.selectedIndexes():
            row = item.row()
            self.log.append( 'item: {}'.format( item ) )
            model.removeRow( row )
            self.log.append( 'Removed row: {}'.format( row ) )
            
            # Unload the media if its streaming       
            media = sources[ row ]
            if media == self.selected_media:
                self.selected_media = None
                self.stop()

            # remove it 
            sources.pop( row )

        # Attempt to select the row
        rows  = self.mediafiles.rowCount()
        self.log.append( 'Rows: {}, removed row: {}'.format( rows, row ) )
        if rows > 0 and row < rows:
            self.selected_media = sources[ row ]
            self.selectRow( row )
        elif rows > 0 and row == rows:
            self.selected_media = sources[ row-1 ]
            self.selectRow( row-1 )            
        else:
            self.preview.clear()

    def update_preview(self):
        # Update preview
        outdir  = cached_path( self.selected_media )
        gif     = '{}.gif'.format( os.path.basename( self.selected_media ) )
        preview = os.path.join( outdir, gif )
        self.log.append( 'Looking for preview: {}, {}'.format( preview, os.path.exists( preview ) ) )
        movie = QMovie( preview )
        self.preview.setMovie( movie )
        movie.start()

    def find( self ):
        folder = FileDialog('Opend')
        self.log.append( '{}'.format( folder.path ) )

        if folder.path is None:
            return # Bail early
        else:
            self.dirname = folder.path

        self.playlist_busy.start()
        self.log.append( 'Sources: {0}'.format( sources ) )
        self.find_btn.setDisabled( True )
        self.add_btn.setDisabled( True )
        self.rm_btn.setDisabled( True )

        self.__updaters = []
        thread = QThread()
        thread.setObjectName( 'Updater' )
        worker = SourceUpdater( 0, self.dirname, icons = self.enable_icons, preview = self.enable_preview )
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
        ''' Busy doing work '''
        pass

    @pyqtSlot( int )
    def discover_done( self, worker_id ):
        self.log.append( 'worker #{} finsihed'.format(worker_id) )
        self.playlist_busy.stop()
        self.find_btn.setEnabled( True )
        self.add_btn.setEnabled( True )
        self.rm_btn.setEnabled( True )

        # Update the list view
        self.build_playlist()

        # Default to the zeroth item
        item = self.mediafiles.index( 0, 0 )
        model = self.playlist.selectionModel()
        model.select( item, QItemSelectionModel.Select)

        # Update the selected media
        if len( sources ) > 0:
            self.selected_media = sources[ 0 ]
            self.log.append( 'Queued: {}'.format( self.selected_media ) )
            self.streamer.path = self.selected_media

            self.update_preview()
            
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
        self.streamer.path  = self.selected_media
        self.update_preview()

    def toggle_icons( self ):
        if self.enable_icons:
            self.enable_icons = False
            self.iconact.setText( 'Enable &Icons' )
        else:
            self.enable_icons = True
            self.iconact.setText( 'Disable &Icons' )
            
    def toggle_preview( self ):
        if self.enable_preview:
            self.enable_preview = False
            self.previewact.setText( 'Enable &Preview' )
        else:
            self.enable_preview = True
            self.previewact.setText( 'Disable &Preview' )
        
    def toggle_log( self ):
        if self.log_shown:
            self.log_shown = False
            self.togglelog.setText( 'Show &Log' )
            self.log.hide()
        else:
            self.log_shown = True
            self.togglelog.setText( 'Hide &Log' )
            self.log.show()
            
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


class SourceUpdater( QObject ):
    sig_step = pyqtSignal(int,int) # Id, step description
    sig_done = pyqtSignal(int)     # Id, end of job
    sig_msg  = pyqtSignal(str)     # msg to user

    def __init__( self, id:int, path:str, icons:bool, preview:bool ):
        super( SourceUpdater, self ).__init__()
        self.__id      = id
        self.__abort   = False
        self.__path    = path
        self.__icons   = icons
        self.__preview = preview

    @pyqtSlot()
    def discover( self ):
        ''' Perform task '''
        thread_name = QThread.currentThread().objectName()
        thread_id   = int( QThread.currentThreadId() )
        msg = 'Running worker #{} from thread "{}" (#{})'.format(self.__id, thread_name, thread_id)
        self.sig_msg.emit(msg)

        # TODO: optimize
        # These are not optimized and chew up resources
        is_ext = lambda f, ext : any( f.endswith( e ) for e in ext )

        t0 = time.time()

        self.sig_msg.emit( 'Clearing sources' )
        sources.clear()

        fcnt = 0
        self.sig_msg.emit( 'Searching...' )
        for root, dirs, files in os.walk( self.__path ):#, topdown=True ):
            files=    [ f for f in files if not f.startswith( '.' ) ]
            dirs[:] = [ d for d in dirs  if not d.startswith( '.' ) ]

            for fname in files:
                fcnt += 1
                self.sig_msg.emit( 'checking root={}, file={}'.format(root, fname ) )
                self.sig_step.emit( 0, fcnt )
                if is_ext( fname.lower(), media_types ):
                    path = os.path.join( root, fname )
                    sources.append( path )
                    if self.__preview: create_gif( path )
                    if self.__icons: create_icon( path )

                # Check for abort
                if self.__abort:
                    self.sig_msg.emit('Aborting')
                    break

        t1 = time.time()
        total = t1 - t0
        self.sig_msg.emit( 'Total time taken: {}'.format( total ) )
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
        self.path     = None
        
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

        stream = stream_media( self.path,
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
