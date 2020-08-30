#!/usr/bin/env python3
import os, sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from v4l2tricks.stream    import stream_media
from v4l2tricks.supported import MediaContainers
from v4l2tricks           import fsutil
from v4l2tricks.ffmpeg_if import create_test_src

def main( args ):
    create_test_src(args.path, duration = args.time_duration )
    
# Standard biolerplate to call the main() function to begin the program
if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser( description='Create test source mp4' )

    # Common parameters
    parser.add_argument( '-p', '--path', help='Output path (defaults: ./testsrc.mp4)', default = './testsrc.mp4' )
    parser.add_argument( '-t', '--time-duration',
                         help   = 'Duration of the test source(defaults: 6 min)',
                         default = 600 )
    parser.add_argument( '-v', '--verbose',
                         help   = 'Increase verbosity',
                         action ='store_true' )

    # Parse the arguments
    args = parser.parse_args()

    # Process the subcommand
    main( args )
