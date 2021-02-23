#!/usr/bin/env python
import os
import sys

from PyQt5.QtCore import QTimer, Qt
from PyQt5.QtWidgets import QApplication, QMainWindow
from PyQt5.QtWidgets import QLabel, QGridLayout, QPushButton, QWidget

# Setup imports from module
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

class StreamScope( QMainWindow ):
    def __init__( self ):
        super().__init__()
        self.setWindowTitle( self.__class__.__name__ )
        self.setGeometry( 32, 32, 320, 200 )


        
        # Setup widgets
        self.stream_btn = QPushButton( self )
        self.stream_btn.setText( 'Stream' )
        self.stream_btn.clicked.connect( self.stream )

        self.stop_btn = QPushButton( self )
        self.stop_btn.setText( 'Stop' )
        self.stop_btn.clicked.connect( self.stop )


        # Pack the layout
        self.grid =   QGridLayout()
        self.grid.addWidget( self.stream_btn, 0, 0 )
        self.grid.addWidget( self.stop_btn,   1, 0 )

        centralWidget = QWidget()
        centralWidget.setLayout( self.grid )
        self.setCentralWidget( centralWidget )

        # Show the window
        self.show()


    def stream( self ):
        print( 'Started' )

    def stop( self ):
        print( 'Stopped' )

# Main
def main():
    print( "hello" )
    app = QApplication( sys.argv )
    ss = StreamScope()
    sys.exit( app.exec_() )
    
# Standard biolerplate to call the main() function to begin the program
if __name__ == '__main__':
    main()


