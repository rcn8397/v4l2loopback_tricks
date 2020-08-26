#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""ffmpeg interfaces
"""
import os
import sys
import pdb

import ffmpeg

def generate_thumbnail(in_filename, out_filename, time=0.1, width=120):
    '''
    Directly from ffmpeg-python examples
    https://github.com/kkroening/ffmpeg-python/blob/master/examples/get_video_thumbnail.py
    '''
    try:
        (
            ffmpeg
            .input(in_filename, ss=time)
            .filter('scale', width, -1)
            .output(out_filename, vframes=1)
            .overwrite_output()
            .run(capture_stdout=True, capture_stderr=True)
        )
    except ffmpeg.Error as e:
        print(str( e ) )#e.stderr.decode(), file=sys.stderr)
        sys.exit(1)

def probe( fname ):
    probe = ffmpeg.probe(fname)
    video_info = next(s for s in probe['streams'] if s['codec_type'] == 'video')
    width = int(video_info['width'])
    height = int(video_info['height'])
    num_frames = int(video_info['nb_frames'])
    return width, height, num_frames

def stream_media( fname, dev = '/dev/video20' ):
    '''
    'ffmpeg -re -i "{0}" -f v4l2 "{1}"'

    Setting -re was obtained from setting re=None
    https://github.com/kkroening/ffmpeg-python/issues/343
    '''
    print( 'Attempting to Stream: {} to {}'.format( fname, dev ) )
    width, height, num_frames = probe( fname )
    print( '{0}: w={1}, h={2}'.format( fname, width, height ) )
    inp = ffmpeg.input( fname, re=None ).output( dev, f='v4l2' )
    print( inp.compile() )

    process = (
        inp.run_async( pipe_stdout = True, pipe_stdin = False)
        )
    out, err = process.communicate()

def create_test_src(path='./testsrc.mp4'):
    '''
    ffmpeg -f lavfi -i testsrc -t 30 -pix_fmt yuv420p testsrc.m4p
    '''
    process = (
        ffmpeg
        .input( 'testsrc', f='lavfi', t= 30  )
        .output( path, pix_fmt='yuv420p' )
        .run_async( pipe_stdout = True, pipe_stdin = False)
        )
    out, err = process.communicate()

# Main
def main():
    print( "hello" )
    testsrc = './testsrc.mp4'
    create_test_src(testsrc)
    stream_media( testsrc )


# Standard biolerplate to call the main() function to begin the program
if __name__ == '__main__':
    main()
