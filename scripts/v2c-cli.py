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

class AppMode( object ):
    STOPPED = 0
    PLAYING = 1
    modes = { STOPPED : 'Stopped',
             PLAYING : 'Playing' }
    def __init__( self, mode = STOPPED ):
        super( AppMode, self ).__init__()
        self._mode = mode

    @staticmethod
    def to_str( mode ):
        try:
            s = AppMode.modes[ mode ]
        except Exception as e:
            s = None
        return s

    def __str__( self ):
        return AppMode.to_str( self.mode )

    @property
    def mode( self ):
        return self._mode

    @mode.setter
    def mode( self, new_mode ):
        self._mode = new_mode

# Console controller
class v2cConsole( cmd.Cmd ):
    '''
    Simple command processor for streaming media to v4l2loopback device
    '''
    active      = None
    state       = AppMode()
    queued      = None
    stream      = None
    prompt_tmpl = '([ {0} ]{1})\n(!>)'
    prompt      = '(!>)'

    # Helpers and procedures
    def update_state( self ):
        self.state.mode = AppMode.STOPPED
        if self.stream is not None and self.Stream.alive:
            self.state.mode = AppMode.PLAYING

    def update_prompt( self ):
        fname = ''
        if self.queued is not None:
            fname = self.queued
        self.prompt = self.prompt_tmpl.format( str( self.state ),
                                               fname )

    # Menu/Commands
    def do_list( self, line ):
        '''
        List media sources loaded
        '''
        print( line )

    def help_list( self ):
        print( '\n'.join( [ 'list',
                            'List media source(s) loaded' ] ) )
    def do_load( self, line ):
        '''
        Load media source(s)
        '''
        print( line )

    def help_load( self ):
        print( '\n'.join( [ 'load',
                            'Load media source(s)' ] ) )

    def do_next( self, line ):
        '''
        Make next source the active source
        '''
        print( line )

    def help_next( self ):
        print( '\n'.join( [ 'next',
                            'Make next source the active source' ] ) )

    def do_stream( self, line ):
        '''
        Stream media to v4l2loopback device
        '''
        print( line )

    def complete_stream( self, text, line, begidx, endidx ):
        if not text:
            completions = self._loaded[:]
        else:
            completions = [ l for l in self._loaded if l.startswith( text ) ]
        return completions

    def help_stream( self ):
        print( '\n'.join( [ 'stream',
                            'Stream media to v4l2loopback device' ] ) )

    def do_stop( self, line ):
        '''
        Stop active stream
        '''
        print( line )

    def help_stop( self ):
        print( '\n'.join( [ 'stop', 'Stops the active stream' ] ) )

    def do_q( self, line ):
        '''
        Exit loop
        '''
        return True

    def help_q( self ):
        print( '\n'.join( [ 'q', 'Exits program' ] ) )

    def do_quit( self, line ):
        '''
        Exit loop
        '''
        return True

    def help_quit( self ):
        print( '\n'.join( [ 'quit', 'Exits program' ] ) )

    #----------------------
    # cmd member overloads
    #----------------------
    def preloop( self ):
        '''
        Setup the environment
        '''
        print( 'Preloop called' )
        self._loaded = [ '1', '2']

    def postloop( self ):
        '''
        Clean up the environment
        '''
        print( 'Postloop called' )

    def precmd(self, line):
        print( 'precmd(%s)' % line )
        self.update_state()
        self.update_prompt()
        return cmd.Cmd.precmd(self, line)

    def postcmd( self, stop, line ):
        print( 'postcmd(%s,%s)' % ( stop, line ) )
        self.update_state()
        self.update_prompt()
        return cmd.Cmd.postcmd(self, stop, line)

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
