#!/usr/bin/env python
'''
Video tutorial
'''
import os, sys
import pdb

import numpy as np
import cv2

def main( args ):
    cap = cv2.VideoCapture( args.device )
    while( cap.isOpened() ):
        # Capture frame-by-frame
        ret, frame, = cap.read()

        # Operates on the frame come here
        gray = cv2.cvtColor( frame, cv2.COLOR_BGR2GRAY )

        # Display the resulting frame
        cv2.imshow( 'Monitor', gray )
        if cv2.waitKey( 1 ) & 0xff == ord( 'q' ):
            break

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
