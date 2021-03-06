#!/usr/bin/env python3
'''
Video tutorial
'''
import os, sys
import pdb

import numpy as np
import cv2

WINDOW_NAME   = 'Monitor'
SCALE_PERCENT = 50

def main( args ):
    cv2.namedWindow( WINDOW_NAME, cv2.WINDOW_NORMAL )
    cap = cv2.VideoCapture( args.device )
    while( cap.isOpened() ):
        # Capture frame-by-frame
        ret, frame, = cap.read()

        # Operates on the frame come here
        frame = cv2.cvtColor( frame, cv2.COLOR_BGR2GRAY )
        
        width  = int( frame.shape[ 1 ] * SCALE_PERCENT / 100 )
        height = int( frame.shape[ 0 ] * SCALE_PERCENT / 100 )
        dsize = ( width, height )

        output = cv2.resize( frame, dsize )
        
        # Display the resulting frame
        cv2.imshow( WINDOW_NAME, output )
        if cv2.waitKey( 1 ) & 0xff == ord( 'q' ):
            break

#       if cv2.getWindowProperty( WINDOW_NAME, cv2.WND_PROP_VISIBLE ) <1:
#           break;
        
    # When everything is done, release the capture device
    cap.release()
    cv2.destroyAllWindows()

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser( description='Tutorial for open CV' )
    parser.add_argument( '-v', '--verbose', action="store_true",
                         help="Increase the verbosity." )
    parser.add_argument( '-d', '--device', 
                         help = 'Device to monitor ("/dev/video20")',
                         default = '/dev/video20' )

    # Parse the arguments
    args = parser.parse_args()
    main( args )
