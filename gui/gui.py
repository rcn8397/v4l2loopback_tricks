#!/usr/bin/env python
import os
import sys

from PyQt5.QtCore import QTimer, Qt
from PyQt5.QtWidgets import QApplication, QMainWindow
from PyQt5.QtWidgets import QLabel, QGridLayout, QPushButton, QWidget
from PyQt5.QtWidgets import QHBoxLayout, QVBoxLayout

# Setup imports from module
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


class StreamScope( QWidget ):
    def __init__( self ):
        super().__init__()
        self.setWindowTitle( self.__class__.__name__ )
        self.setGeometry( 32, 32, 320, 200 )

        self.init_layout()
        
        # Show the window
        self.show()


    def init_layout( self ):
        layout1 = QVBoxLayout()
        layout2 = QHBoxLayout()

        stream_btn = QPushButton( self )
        stream_btn.setText( 'Stream' )
        stream_btn.clicked.connect( self.stream )

        stop_btn = QPushButton( self )
        stop_btn.setText( 'Stop' )
        stop_btn.clicked.connect( self.stop )

        layout2.addWidget( stream_btn )
        layout2.addWidget( stop_btn )

        self.viewfinder = QLabel()
        self.viewfinder.setStyleSheet( 'background-color: cyan; border:5px solid black; background:transparent; ' )
        layout1.addWidget( self.viewfinder )
        layout1.addLayout( layout2 )

        self.setAttribute( Qt.WA_TranslucentBackground )
        self.setLayout( layout1 )
        
    def stream( self ):
        print( 'Started' )
        self.viewfinder.setStyleSheet( 'background-color: cyan; border:5px solid red; background:transparent; ' )

    def stop( self ):
        print( 'Stopped' )
        self.viewfinder.setStyleSheet( 'background-color: cyan; border:5px solid black; background:transparent; ' )

# Main
def main():
    print( "hello" )
    app = QApplication( sys.argv )
    ss = StreamScope()
    sys.exit( app.exec_() )
    
# Standard biolerplate to call the main() function to begin the program
if __name__ == '__main__':
    main()


