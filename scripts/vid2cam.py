#!/usr/bin/env python3

import os
import sys
import pdb
from process import Process

def stream_video( fname, dev ='/dev/video1', verbose = True ):
    '''
    Stream the video <fname> to <dev> (defaults to '/dev/video1')

    Notes:  Per the producer section of the v4l2loopback wiki.
    '''
    cmd = 'ffmpeg -re -i "{0}" -f v4l2 "{1}"'
    p = Process( cmd.format( fname, dev ) )
    if verbose:
        for line in p.output():
            print( line )

# Main
def main(args):
    stream_video( args.source )
    
    
# Standard biolerplate to call the main() function to begin the program
if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser( description='Stream a video to v4l2 loopback device' )
    parser.add_argument( 'source', help = 'Source to stream' )
    parser.add_argument( '-v', '--verbose', help = 'Increase verbosity',
                         action='store_true' )

    main(parser.parse_args())
