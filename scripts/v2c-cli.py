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
    sink        = '/dev/video0'
    loaded      = set()
    prompt_tmpl = '([ {0} : {1} ]{2})\n(!>)'
    prompt      = prompt_tmpl.format( str( state ), sink, '' )

    # Helpers and procedures
    def load_sources( self, path ):
        containers  = MediaContainers()
        media_types = containers.extensions()

        found = None
        pre_load = len( self.loaded )
        if os.path.exists( path ):
            found = fsutil.find( path, media_types )
            self.loaded.update( found )

        if found is not None:
            print( 'Loaded:' )
            for i, fname in enumerate( self.loaded ):
                print( '[{0}]: {1}'.format( i, fname ) )
        print( 'Finished!' )
        num_found = len( found )
        post_load = len( self.loaded )
        total_loaded = post_load - pre_load
        print( 'Found {0}, new media loaded {1}'.format( num_found,
                                                         total_loaded ) )

    def update_state( self ):
        self.state.mode = AppMode.STOPPED
        if self.stream is not None and self.stream.alive:
            self.state.mode = AppMode.PLAYING

    def update_prompt( self ):
        fname = ''
        if self.queued is not None:
            fname = self.queued
        self.prompt = self.prompt_tmpl.format( str( self.state ),
                                               self.sink,
                                               fname )

    def update_sink( self, sink ):
        if os.path.exists( sink ) and '/dev/video' in sink:
            self.sink = sink
            print( 'Sink set to {0}'.format( sink ) )
        else:
            print( 'Could not set sink to {0}'.format( sink ) )


    # Menu/Commands
    def do_list( self, line ):
        '''
        List media sources loaded
        '''
        loaded = list( self.loaded )
        for i, source in enumerate( loaded ):
            print( '[{0}]: {1}'.format( i, source ) )

    def help_list( self ):
        print( '\n'.join( [ 'list',
                            'List media source(s) loaded' ] ) )
    def do_load( self, line ):
        '''
        Load media source(s)
        '''
        print( 'Loading all media sources @ [{0}]'.format( line ) )
        path = os.path.expanduser( line )
        self.load_sources( path )

    def complete_load( self, text, line, begidx, endidx ):
        _,path = line.split( 'load ' )
        path = os.path.expanduser( path )
        if os.path.exists( path ):
              completions = fsutil.list_dir( path )
        else:
            dlist = fsutil.list_dir( os.path.dirname( path ) )
            completions = [ n for n in dlist if n.startswith( text ) ]
        return completions

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
    def do_sink( self, line ):
        '''
        Set the device sink
        '''
        self.update_sink( line )

    def help_sink( self ):
        print( '\n'.join( [ 'sink',
                            'Device sink [{0}'.format( self.sink ) ] ) )

    def complete_sink( self, text, line, begidx, endidx ):
        _,path = line.split( 'sink ' )
        path = os.path.expanduser( path )
        if os.path.exists( path ):
              completions = fsutil.list_dir( path )
        else:
            dlist = fsutil.list_dir( os.path.dirname( path ) )
            completions = [ n for n in dlist if n.startswith( text ) ]
        return completions

    def do_stream( self, line ):
        '''
        Stream media to v4l2loopback device
        '''
        if self.state.mode == AppMode.PLAYING:
            print( 'Stream already started' )
        else:
            print( 'Starting Stream for {0}'.format( line ) )
            loaded  = list( self.loaded )
            sources = [ os.path.basename( s ) for s in loaded ]
            try:
                index = sources.index( line )
            except ValueError as e:
                index = None

            self.active = index

            try:
                source = loaded[ index ]
            except ValueError as e:
                source = None

            print( 'Source: {0}'.format( source ) )
            self.stream = stream_media( source, self.sink )

    def complete_stream( self, text, line, begidx, endidx ):
        loaded = list( self.loaded )
        sources = [ os.path.basename( s ) for s in loaded ]


        if not text:
            completions = sources[:]
        else:
            completions = [ s
                            for s in sources
                            if s.startswith(text)
            ]
        return completions

    def help_stream( self ):
        print( '\n'.join( [ 'stream',
                            'Stream media to v4l2loopback device' ] ) )

    def do_stop( self, line ):
        '''
        Stop active stream
        '''
        print( line )
        if self.stream.alive:
            print( 'Stopping Stream' )
            self.stream.stop()

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
        self.update_state()
        self.update_prompt()

    def postloop( self ):
        '''
        Clean up the environment
        '''
        print( 'Postloop called' )

    def precmd(self, line):
        self.update_state()
        self.update_prompt()
        return cmd.Cmd.precmd(self, line)

    def postcmd( self, stop, line ):
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
    console = v2cConsole()
    if args.source is not None:
        console.load_sources( args.source )

    console.update_sink( args.out )
    console.cmdloop()


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

    parser.add_argument( '-s', '--source',
                         help = 'Source to stream',
                         default = None )
    parser.add_argument( '-o', '--out',
                         help = 'Device to stream to ("/dev/video0")',
                         default = '/dev/video0' )

    # Parse the arguments
    args = parser.parse_args()
    main( args )
