#!/usr/bin/env python
import os
import sys

from PyQt5.QtCore    import QTimer, Qt, QEvent, pyqtSignal, QThread, QObject
from PyQt5.QtWidgets import QApplication, QMainWindow
from PyQt5.QtWidgets import QLabel, QGridLayout, QPushButton, QWidget, QComboBox, QScrollArea
from PyQt5.QtWidgets import QHBoxLayout, QVBoxLayout

# Setup imports from module
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


get_video_devices = lambda : [ dev for dev in os.listdir('/dev') if 'video' in dev ]


class StreamScope( QWidget ):
    resize_signal = pyqtSignal(int)
    def __init__( self ):
        super().__init__()
        self.devices       = get_video_devices()
        self.device        = self.devices[0]
        self.stream_thread = QThread()
        self.streamer      = DeskStreamer()
        self.streamer.moveToThread( self.stream_thread )
        self.stream_thread.start()
        self.stream_thread.started.connect( self.streamer.long_running )
        
        self.setWindowTitle( self.__class__.__name__ )
        self.setGeometry( 32, 32, 320, 200 )       
        
        self.init_layout()
        
        # Show the window
        self.show()


    def init_layout( self ):
        layout1 = QVBoxLayout()
        layout2 = QHBoxLayout()

        # Get video devices
        combo      = QComboBox( self )
        for device in self.devices:
            combo.addItem( device )
        combo.activated[str].connect( self.comboChanged )
        
        stream_btn = QPushButton( self )
        stream_btn.setText( 'Stream' )
        stream_btn.clicked.connect( self.stream )

        stop_btn = QPushButton( self )
        stop_btn.setText( 'Stop' )
        stop_btn.clicked.connect( self.stop )

        layout2.addWidget( stream_btn )
        layout2.addWidget( stop_btn )
        layout2.addWidget( combo )

        self.viewfinder = QLabel()
        self.viewfinder.setStyleSheet( 'background-color: cyan; border:5px solid orange; background:transparent; ' )
        layout1.addWidget( self.viewfinder )
        layout1.addLayout( layout2 )

        self.setAttribute( Qt.WA_TranslucentBackground )
        self.setLayout( layout1 )
        
    def stream( self ):
        print( 'Started' )
        self.viewfinder.setStyleSheet( 'background-color: cyan; border:5px solid red; background:transparent; ' )
        self.streamer.stream()

    def stop( self ):
        print( 'Stopped' )
        self.viewfinder.setStyleSheet( 'background-color: cyan; border:5px solid orange; background:transparent; ' )
        self.streamer.stop()

    def comboChanged( self, text ):
        self.device = text

    def update_frustum( self ):
        print( 'Window: {0}'.format( self.pos() ) )
        print( 'Scope:  {0}, {1}x{2}'.format( self.viewfinder.pos(),self.viewfinder.width(), self.viewfinder.height() ) )
        print( 'Device: {0}'.format( self.device ) )

    def moveEvent( self, event ):
        self.update_frustum()
        super().moveEvent(event)

    def resizeEvent(self, event = None):
        self.update_frustum()
        self.resize_signal.emit( 1 )


class DeskStreamer( QObject ):
    finished = pyqtSignal()

    def __init__( self ):
        super(DeskStreamer, self).__init__()
        self._running = True
        self._exit    = False

    def stream( self ):
        self._running = True
        
    def stop( self ):
        self._running = False
        
    def long_running( self ):
        import time
        count = 0
        while not self._exit:
            if self._running:
                time.sleep(1)
                print("A Increasing")
                count += 1
        self.finished.emit()

    def process_stream( stream ):
        while stream.alive:
            try:
                line  = stream.readline
                if line is not None:
                    print( line )
            except KeyboardInterrupt:
                pass
        print( 'Bye' )
        
    def dsk_stream( args ):
        display = ':1'
        if args.display is None:
            try:
                display = os.environ[ 'DISPLAY' ]
            except KeyError as e:
                print( 'Could not detect DISPLAY variable (normally :0 or :1)' )
                pass
    
        stream = desktop_stream( args.x,
                                 args.y,
                                 args.width,
                                 args.height,
                                 display,
                                 args.out,
                                 args.verbose )
        process_stream( stream )
            
            
# Main
def main():
    app = QApplication( sys.argv )
    ss = StreamScope()    
    sys.exit( app.exec_() )
    
# Standard biolerplate to call the main() function to begin the program
if __name__ == '__main__':
    main()


