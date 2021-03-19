#!/usr/bin/env python3
'''
Original implementation found @
https://github.com/snowwlex/QtWaitingSpinner/blob/master/waitingspinnerwidget.cpp

License: MIT
'''

import os
import sys
import time
import math
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *

class QtWaitSpinner(QWidget):
    _color                = QColor( Qt.black )
    _roundness            = 100.0
    _minimumTrailOpacity  = 50
    _trailFadePercentage  = 50
    _revolutionsPerSecond = math.pi/2
    _numberOfLines        = 20
    _lineLength           = 10
    _lineWidth            = 2
    _innerRadius          = 20
    _currentCounter       = 0
    _isSpinning           = False

    @property
    def minTrailOpacity( self ):
        return self._minimumTrailOpacity

    @minTrailOpacity.setter
    def minTrailOpacity( self, v ):
        self._minimumTrailOpacity = v

    @property
    def trailFadePercent( self ):
        return self._trailFadePercentage

    @trailFadePercent.setter
    def trailFadePercent( self, v ):
        self._trailFadePercentage = v

    def getColor( self ):
        return self._color 

    def setColor( self, color ):
        self._color = color
        
    def __init__( self, parent = None,  centerOnParent = True, disableParent = True ):
        super( QtWaitSpinner, self ).__init__( parent )

        self._centerOnParent = centerOnParent
        self._disableParentWhenSpinning = disableParent

        self._timer = QTimer(self);
        self._timer.timeout.connect( self.rotate )
        self.updateSize()
        self.updateTimer()
        self.hide()

    def lineCountDistanceFromPrimary( self, current, primary, totalNrOfLines ):
        distance = primary - current
        if distance < 0:
            distance += totalNrOfLines
        return distance

    def currentLineColor( self, countDistance, totalNrOfLines, trailFadePerc, minOpacity, color ):
        if countDistance == 0:
            return color
        
        minAlphaF = minOpacity / 100.0
        
        distanceThreshold = math.ceil( (totalNrOfLines - 1 ) * trailFadePerc / 100.0 )
        if countDistance > distanceThreshold:
            color.setAlphaF( minAlphaF )
        else:
            alphaDiff = self._color.alphaF() - minAlphaF
            gradient  = alphaDiff / distanceThreshold + 1.0
            resultAlpha = color.alphaF() - gradient * countDistance
            # Clip the result
            resultAlpha = min( 1.0, max( 0.0, resultAlpha ) )
            color.setAlphaF( resultAlpha )

        return color
            

    def debug( self ):
        for x in vars( self ):
            print( '{} = {}'.format( x, vars( self )[x] ) )
        print( 'Parent Widget: {}'.format( self.parentWidget() ) )
        print( 'Color Name: {}'.format( self._color.name() ) )
            
    def paintEvent( self, event ):
        ''' Overload paintEvent '''
        self.updatePosition()
        painter = QPainter( self )
        painter.fillRect( self.rect(), Qt.transparent )
        painter.setRenderHint( QPainter.Antialiasing, True )

        if self._currentCounter >= self._numberOfLines:
            self._currentCounter = 0

        painter.setPen( Qt.NoPen )
        for i in range( self._numberOfLines ):
            painter.save()
            painter.translate( self._innerRadius + self._lineLength,
                               self._innerRadius + self._lineLength )

            assert( self._numberOfLines > 0 ) # Check 4 zero
            rotateAngle = ( 360 * i ) / self._numberOfLines 
            painter.rotate( rotateAngle )
            painter.translate( self._innerRadius, 0 )

            distance = self.lineCountDistanceFromPrimary( i, self._currentCounter, self._numberOfLines )
            color    = self.currentLineColor( distance,
                                         self._numberOfLines,
                                         self._trailFadePercentage,
                                         self._minimumTrailOpacity,
                                         self._color )
            painter.setBrush( color )
            painter.drawRoundedRect( QRect( 0,
                                            -self._lineWidth / 2,
                                            self._lineLength,
                                            self._lineWidth ),
                                     self._roundness,
                                     self._roundness,
                                     Qt.RelativeSize )
            painter.restore()
            

    @pyqtSlot()
    def rotate( self ):
        self._currentCounter += 1
        if self._currentCounter > self._numberOfLines:
           self._currentCounter = 0
        self.update()

    def start( self ):
        self.updatePosition()
        self._isSpinning = True
        self.show()

        if self.parentWidget() and self._disableParentWhenSpinning:
            self.parentWidget().setEnabled( False )

        if not self._timer.isActive():
            self._timer.start()
            self._currentCounter = 0

    def stop( self ):
        self._isSpinning = False
        self.hide()

        if self.parentWidget() and self._disableParentWhenSpinning:
            self.parentWidget().setEnabled( True )

        if self._timer.isActive():
            self._timer.stop()
            self._currentCounter = 0
        
    def updatePosition( self ):
        if self.parentWidget() and self._centerOnParent:
            self.move( self.parentWidget().width() / 2 - self.width() / 2,
                       self.parentWidget().height() / 2 - self.height() / 2 )

    def updateSize( self ):
        size = ( self._innerRadius + self._lineLength ) * 2
        self.setFixedSize( size, size )

    def updateTimer( self ):
        self._timer.setInterval( 1000 / ( self._numberOfLines * self._revolutionsPerSecond ) )

    

class TestWindow( QWidget ):
    def __init__(self ):
        super().__init__()
        label = QLabel('Testing', self )
        label.setFixedWidth( 320 )
        label.setFixedHeight( 320 )

        
        self.busy = QtWaitSpinner( label, centerOnParent = True, disableParent = True )

        layout = QVBoxLayout()
        self.trans_value = QLabel( str( self.busy._trailFadePercentage ), self )
        self.mintrans_value = QLabel( str( self.busy._minimumTrailOpacity ), self )

        self.trans = QSlider( Qt.Horizontal )
        self.trans.setMinimum( 0.0 )
        self.trans.setMaximum( 100.0 )
        self.trans.setValue(20)
        self.trans.valueChanged.connect( self.set_trans )
        
        self.mins = QSlider( Qt.Horizontal )
        self.mins.setMinimum( 0.0 )
        self.mins.setMaximum( 100.0 )
        self.mins.setValue( 20 )
        self.mins.valueChanged.connect( self.set_mins )

        start = QPushButton( self )
        start.setText( 'start' )
        start.clicked.connect( self.busy.start )

        stop = QPushButton( self )
        stop.setText( 'stop' )
        stop.clicked.connect( self.busy.stop )
        
        layout.addWidget( label )
        layout.addWidget( self.trans_value )
        layout.addWidget( self.mintrans_value )
        layout.addWidget( self.trans )
        layout.addWidget( self.mins )
        layout.addWidget(start)
        layout.addWidget(stop)
        self.setLayout( layout )       

        self.setWindowTitle('Absolute')
        self.show()

    def set_trans( self ):
        self.trans_value.setText( str( self.trans.value() ) )
        self.busy._trailFadePercentage = self.trans.value()

    def set_mins( self ):
        self.mintrans_value.setText( str( self.mins.value() ) )
        self.busy._minimumTrailOpacity = self.mins.value()

        
# Main
def main():
    app = QApplication( sys.argv )
    test = TestWindow()   
    sys.exit( app.exec_() )

# Standard biolerplate to call the main() function to begin the program
if __name__ == '__main__':
    main()
