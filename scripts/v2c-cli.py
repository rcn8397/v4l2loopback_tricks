#!/usr/bin/env python3
import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from v4l2tricks.stream    import stream_media
from v4l2tricks.supported import MediaContainers
from v4l2tricks           import fsutil

import cmd

# Get media from filesystem subtree
def get_media( path ):
    containers = MediaContainers()
    media_types = containers.extensions()
    return fsutil.find( args.path, media_types )

# Stream a media files to device
def fil_stream(args):
    stream = stream_media( args.source, args.out )
    print( 'Streaming: {0}'.format( stream.alive ) )
    try:
        assert( stream.alive )
    except AssertionError as e:
        stream.dump()

# Console controller
class v2cConsole( cmd.Cmd ):
    '''
    Simple command processor for streaming media to v4l2loopback device
    '''
    def do_list( self, line ):
        '''
        List media sources loaded
        '''
        print( line )

    def do_load( self, line ):
        '''
        Load media source(s)
        '''
        print( line )

    def do_next( self, line ):
        '''
        Make next source the active source
        '''
        print( line )

    def do_stream( self, line ):
        '''
        Stream media to v4l2loopback device
        '''
        print( line )

    def do_stop( self, line ):
        '''
        Stop active stream
        '''
        print( line )

    def do_q( self, line ):
        '''
        Exit loop
        '''
        return True

    def do_quit( self, line ):
        '''
        Exit loop
        '''
        return True

    #----------------------
    # cmd member overloads
    #----------------------
    def preloop( self ):
        '''
        Setup the environment
        '''
        print( 'Preloop called' )

    def postloop( self ):
        '''
        Clean up the environment
        '''
        print( 'Postloop called' )

    def do_EOF( self, line ):
        '''
        Exit cleanly when EOF is received
        '''
        return True


def main( args ):
    '''
    Main entry point
    '''
    print( args )
    v2cConsole().cmdloop()


# Standard biolerplate to call the main() function to begin the program
if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser( description='CLI control of Stream to v4l2 loopback device' )

    # Parameters
    parser.add_argument( '-l', '--loop',
                         help   = 'Loop indefinitely.',
                         action = 'store_true' )
    parser.add_argument( '-v', '--verbose',
                         help   = 'Increase verbosity',
                         action ='store_true' )

    parser.add_argument( 'source',
                             help = 'Source to stream' )
    parser.add_argument( '-o', '--out',
                         help = 'Device to stream to ("/dev/video1")',
                         default = '/dev/video1' )

    # Parse the arguments
    args = parser.parse_args()
    main( args )
