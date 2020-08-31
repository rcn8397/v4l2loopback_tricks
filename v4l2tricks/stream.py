# -*- coding: utf-8 -*-
"""ffmpeg interfaces
"""
from .ffmpeg_if import StreamProcess, OverlayStreamProcess, DesktopStreamProcess

def stream_media( fname, dev ='/dev/video20', verbose = True ):
    '''
    Stream the video <fname> to <dev> (defaults to '/dev/video1')

    Notes:  Per the producer section of the v4l2loopback wiki.
    ffmpeg -re -i "{0}" -f v4l2 "{1}"
    '''
    return StreamProcess( fname, dev, verbose )


def overlay_stream( fname, overlay, dev = '/dev/video20', verbose = True ):
    return OverlayStreamProcess( fname, overlay, dev, verbose )


def desktop_stream( x = 0, y = 0, w = 640, h = 480, display = ':0', dev = '/dev/video20', verbose = True ):
    return DesktopStreamProcess( x, y, w, h, display,  dev, verbose )
