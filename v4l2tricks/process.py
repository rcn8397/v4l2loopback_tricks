# -*- coding: utf-8 -*-
"""Subprocess - tools
"""
from subprocess import Popen, PIPE,STDOUT,DEVNULL
import shlex

class Subprocess( object ):
    '''
    Subprocess object
    '''
    def __init__( self, cmd = [ 'echo', 'hello world' ], block = True ):
        super( Subprocess, self ).__init__()
        self._cmd = cmd
        self._stdout = []
        self._output = ''

        if block:
            mode = PIPE
        else:
            mode = DEVNULL
            
        self._proc = Popen( cmd,
                            stdout             = mode,
                            stderr             = STDOUT,
                            shell              = False,
                            encoding           = 'utf-8',
                            universal_newlines = True,
                            bufsize            = 1 )
        if block:
            with self._proc.stdout:
                for line in iter( self._proc.stdout.readline, b'' ):
                    self._stdout.append( line )
                self._proc.wait()

    @property
    def readline( self ):
        return self._proc.stdout.readline()

    def read( self, bufsize = 80 ):
        self._output += self._proc.stdout.read( bufsize )

    @property
    def alive( self ):
        alive = self._proc.poll() == None
        return alive

    def stop( self ):
        self._proc.kill()

    def dump( self ):
        for line in self.readline:
            print( line )


class Process( Subprocess ):
    '''
    Simple Subprocess interface
    '''
    def __init__( self, cmd = 'echo "hello world"', block = True ):
        super( Process, self ).__init__( shlex.split( cmd ), block )
