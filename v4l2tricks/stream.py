# -*- coding: utf-8 -*-
"""ffmpeg interfaces
"""
from .ffmpeg_if import StreamProcess, OverlayStreamProcess

def stream_media( fname, dev ='/dev/video20' ):
    '''
    Stream the video <fname> to <dev> (defaults to '/dev/video1')

    Notes:  Per the producer section of the v4l2loopback wiki.
    ffmpeg -re -i "{0}" -f v4l2 "{1}"
    '''
    return StreamProcess( fname, dev )


def overlay_stream( fname, overlay, dev = '/dev/video20' ):
    return OverlayStreamProcess( fname, overlay, dev )
