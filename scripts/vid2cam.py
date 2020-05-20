#!/usr/bin/env python3
import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from v4l2tricks.stream  import stream_media

# Stream a media files to device
def fil_stream(args):
    stream = stream_media( args.source, args.out, verbose = False )
    print( 'Streaming: {0}'.format( stream.alive ) )
    while stream.alive:
        if args.verbose:
            print( stream.readline )

            
# Stream a list of media files to device
def dir_stream( args ):
    print( args )

    
# Standard biolerplate to call the main() function to begin the program
if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser( description='Stream a video to v4l2 loopback device' )

    # Create subparser
    subparsers = parser.add_subparsers( help='Sub-commands' )
    
    #-------------------------
    # Single Media File
    #-------------------------
    parser_fil = subparsers.add_parser( 'fil', help = 'Stream file to device' )
    parser_fil.add_argument( 'source',
                             help = 'Source to stream' )
    parser_fil.add_argument( '-o', '--out',
                             help = 'Device to stream to ("/dev/video1")',
                             default = '/dev/video1' )
    parser_fil.add_argument( '-v', '--verbose',
                             help   = 'Increase verbosity',
                             action ='store_true' )
    
    parser_fil.set_defaults( func = fil_stream )

    #-------------------------
    # Dir tree of media files
    #-------------------------
    parser_dir = subparsers.add_parser( 'dir', help = 'Stream files in directory subtree to device' )
    parser_dir.add_argument( 'path', help = 'Path to media files.' )
    parser_dir.add_argument( '-o', '--out',
                             help = 'Device to stream to ("/dev/video1")',
                             default = '/dev/video1' )

    parser_dir.add_argument( '-v', '--verbose', 
                             help   = 'Increase the verbosity.',
                             action = 'store_true' )
    parser_dir.set_defaults( func = dir_stream )

    #-------------------------
    # Help
    #-------------------------
    parser_help = subparsers.add_parser( 'help', help = 'Print help' )
    def help_please(): pass
    parser_help.set_defaults( func = help_please )

    # Parse the arguments
    args = parser.parse_args()

    if args.func == help_please:
        parser.print_help()
        sys.exit( 0 )

    # Process the subcommand
    args.func( args )
