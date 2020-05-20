# -*- coding: utf-8 -*-
"""ffmpeg interfaces
"""
from .process import Process

def stream_media( fname, dev ='/dev/video1', verbose = True ):
    '''
    Stream the video <fname> to <dev> (defaults to '/dev/video1')

    Notes:  Per the producer section of the v4l2loopback wiki.
    '''
    cmd = 'ffmpeg -re -i "{0}" -f v4l2 "{1}"'
    stream = Process( cmd.format( fname, dev ), False )
    return stream
