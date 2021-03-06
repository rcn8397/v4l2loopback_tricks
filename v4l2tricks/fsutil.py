# -*- coding: utf-8 -*-
"""File System - tools
"""

import os

def find( path, patterns ):
     '''
     Find all files with ext patterns
     '''
     is_ext = lambda f, ext : any( f.endswith( e ) for e in ext )
     matches = []
     for root, dirs, files in os.walk( path, topdown=True ):
         for filename in files:
             if is_ext( filename.lower(), patterns ):
                 match = os.path.join( root, filename )
                 matches.append( match )
     return matches

# Attempt to get a list of a filesystem subtree from a string
def list_dir( path = None ):
    dirlist = []
    if path is None:
        path = '.'
    try:
        dirlist = os.listdir( path )
    except Exception as e:
        pass
    return dirlist
