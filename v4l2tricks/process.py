# -*- coding: utf-8 -*-
"""Subprocess - tools
"""
from subprocess import Popen, PIPE
import shlex

class Subprocess( object ):
    '''
    Subprocess object
    '''
    def __init__( self, cmd = [ 'echo', 'hello world' ] ):
        super( Subprocess, self ).__init__()
        self._cmd = cmd
        self._stdout = []
        self._proc = Popen( cmd, stdout=PIPE, bufsize=1 )
        with self._proc.stdout:
            for line in iter( self._proc.stdout.readline, b'' ):
                self._stdout.append( line )
        self._proc.wait()

    def output( self ):
        for line in self._stdout:
            yield line

    def dump( self ):
        for line in self._stdout:
            print( line )
            

class Process( Subprocess ):
    '''
    Simple Subprocess interface
    '''
    def __init__( self, cmd = 'echo "hello world"' ):
        super( Process, self ).__init__( shlex.split( cmd ) )
