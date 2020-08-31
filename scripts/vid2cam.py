#!/usr/bin/env python
import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from v4l2tricks.stream    import stream_media, overlay_stream, desktop_stream
from v4l2tricks.supported import MediaContainers
from v4l2tricks           import fsutil


# Stream the desktop to device
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
                             args.out )
    while stream.alive:
        if args.verbose:
            line = stream.readline
            if line is not None: print( line )

# Stream a media files to device
def fil_stream(args):
    if args.overlay is None:
        stream = stream_media( args.source, args.out )
    else:
        stream = overlay_stream( args.source, args.overlay, args.out )
    print( 'Streaming: {0}'.format( stream.alive ) )
    while stream.alive:
        if args.verbose:
            print( stream.readline )


# Stream a list of media files to device
def dir_stream( args ):
    print( args )
    containers = MediaContainers()
    media_types = containers.extensions()
    print( media_types )

    found = fsutil.find( args.path, media_types )
    while True:
        for source in found:
            stream = stream_media( source, args.out )
            while stream.alive:
                if args.verbose:
                    print( stream.readline )

        if not args.loop:
            break
    print( 'Finished' )


# Standard biolerplate to call the main() function to begin the program
if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser( description='Stream a video to v4l2 loopback device' )

    # Common parameters
    parser.add_argument( '-l', '--loop',
                         help   = 'Loop indefinitely.',
                         action = 'store_true' )
    parser.add_argument( '-v', '--verbose',
                         help   = 'Increase verbosity',
                         action ='store_true' )

    # Create subparser
    subparsers = parser.add_subparsers( help='Sub-commands' )

    #-------------------------
    # Single Media File
    #-------------------------
    parser_fil = subparsers.add_parser( 'fil', help = 'Stream file to device' )
    parser_fil.add_argument( 'source',
                             help = 'Source to stream' )
    parser_fil.add_argument( '-o', '--out',
                             help = 'Device to stream to ("/dev/video20")',
                             default = '/dev/video20' )
    parser_fil.add_argument( '--overlay',
                             help = 'Overlay input', default = None  )
    parser_fil.set_defaults( func = fil_stream )

    #-------------------------
    # Dir tree of media files
    #-------------------------
    parser_dir = subparsers.add_parser( 'dir', help = 'Stream files in directory subtree to device' )
    parser_dir.add_argument( 'path', help = 'Path to media files.' )
    parser_dir.add_argument( '-o', '--out',
                             help = 'Device to stream to ("/dev/video20")',
                             default = '/dev/video20' )

    parser_dir.set_defaults( func = dir_stream )


    #-------------------------
    # Desktop of media files
    #-------------------------
    parser_dsk = subparsers.add_parser( 'dsk', help = 'Stream desktop at x, y with size of sizex, sizey to device' )
    parser_dsk.add_argument( '-x', help = 'X position of the desktop', default = 0 )
    parser_dsk.add_argument( '-y', help = 'Y position of the desktop', default = 0 )
    parser_dsk.add_argument( '--width',
                             help = 'Width of the desktop to stream', default = 640 )
    parser_dsk.add_argument( '--height',
                             help = 'Height of the desktop to stream', default = 480 )
    parser_dsk.add_argument( '-d', '--display',
                             help = 'Display ID', default = None )
    parser_dsk.add_argument( '-o', '--out',
                             help = 'Device to stream to ("/dev/video20")',
                             default = '/dev/video20' )

    parser_dsk.set_defaults( func = dsk_stream )

    

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
