#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Supported media formats.
https://kodi.wiki/view/Features_and_supported_formats

Media containers:
AVI, MPEG, WMV, ASF, FLV, MKV/MKA (Matroska), QuickTime, MP4, M4A, AAC, NUT, Ogg, OGM, RealMedia RAM/RM/RV/RA/RMVB, 3gp, VIVO, PVA, NUV, NSV, NSA, FLI, FLC, DVR-MS, WTV, TRP and F4V
"""

class MediaContainers( object ):
    def __init__( self ):
        self._supported = [ Mpeg1(),
                            Mpeg2(),
                            Mpeg4(),
                            QuickTime(),
                            RealMedia(),
                            Vp9(),
                            Wmv(),
                            Asf(),
                            Flash(),
                            Matroska(),
                            Ogg(),
                            ThreeGp(),
                            DivX(),
                            Vob(),
                            Bluray() ]

        self._file_extensions = []
        
    def extensions( self, wildcard=False ):
        extensions = []
        for media in self._supported:
            extensions.extend( media.fs_ext( wildcard ) )
        return set( extensions )

        
class SupportedMedia( object ):
    def __init__( self ):
        super( SupportedMedia, self ).__init__()
    
    def fs_ext( self, wildcard = True ):
        return [ '*%s' % ext if wildcard else ext for ext in self._extensions ] 

class Mpeg1( SupportedMedia ):
    def __init__( self ):
        super( Mpeg1, self ).__init__()
        self._extensions = [ '.mpg', '.mpeg', '.mp1', '.mp2', '.mp3', '.m1v', '.m1a','.m2a', '.mpa', '.mpv' ]

class Mpeg2( Mpeg1 ):
    def __init__( self ):
        super( Mpeg2, self ).__init__()

class Mpeg4( SupportedMedia ):
    def __init__( self ):
        super( Mpeg4, self ).__init__()
        self._extensions = [ '.mp4', '.m4a', '.m4p', '.m4b', '.m4r', '.m4v' ]

class QuickTime( SupportedMedia ):
    def __init__( self ):
        super( QuickTime, self ).__init__()
        self._extensions = [ '.mov', '.qt' ]

class RealMedia( SupportedMedia ):
    def __init__( self ):
        super( RealMedia, self ).__init__()
        self._extensions = ['.rmvb']

class Vp9( SupportedMedia ):
    def __init__( self ):
        super( Vp9, self ).__init__()
        self._extensions = ['.webm', '.mkv']

class Wmv( SupportedMedia ):
    '''
    Windows Media Video
    '''
    def __init__( self ):
        super( Wmv, self ).__init__()
        self._extensions = ['.wmv', '.asf', '.avi']

class Asf( SupportedMedia ):
    '''
    AdvancedSystemsFormat
    ''' 
    def __init__( self ):
        super( Asf, self ).__init__()
        self._extensions = [ '.asf', '.wma', '.wmv' ]

class Flash( SupportedMedia ):
    def __init__( self ):
        super( Flash, self ).__init__()
        self._extensions = [ '.flv', '.f4v', '.f4p', '.f4a', '.f4b' ]


class Matroska( SupportedMedia ):
    def __init__( self ):
        super( Matroska, self ).__init__()
        self._extensions = [ '.mkv', '.mk3d', '.mka', '.mks' ]

class Ogg( SupportedMedia ):
    def __init__( self ):
        super( Ogg, self ).__init__()
        self._extensions = [ '.ogg', '.ogv', '.oga', '.ogx', '.ogm', '.spx', '.opus' ]


class ThreeGp( SupportedMedia ):
    def __init__( self ):
        super( ThreeGp, self ).__init__()
        self._extensions = [ '.3gp' ]

class DivX( SupportedMedia ):
    def __init__( self ):
        super( DivX, self ).__init__()
        self._extensions = [ '.avi', '.divx', '.mkv' ]

class Vob( SupportedMedia ):
    def __init__( self ):
        super( Vob, self ).__init__()
        self._extensions = [ '.vob' ]

class Bluray( SupportedMedia ):
    def __init__( self ):
        super( Bluray, self ).__init__()
        self._extensions = [ '.m2ts', '.mts' ]

        
