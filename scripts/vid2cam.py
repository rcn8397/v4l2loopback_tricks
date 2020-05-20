#!/usr/bin/env python3
import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from v4l2tricks.stream  import stream_media

# Main
def main(args):
    stream_media( args.source, args.out, verbose = False )
    
    
# Standard biolerplate to call the main() function to begin the program
if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser( description='Stream a video to v4l2 loopback device' )
    parser.add_argument( 'source',
                         help = 'Source to stream' )
    parser.add_argument( '-o', '--out',
                         help = 'Device to stream to ("/dev/video1")',
                         default='/dev/video1' )
    parser.add_argument( '-v', '--verbose',
                         help = 'Increase verbosity',
                         action='store_true' )

    main(parser.parse_args())
