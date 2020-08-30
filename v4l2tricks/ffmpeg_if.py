#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""ffmpeg interfaces
"""
import os
import sys
import ffmpeg
from threading import Thread

try:
    from queue import Queue, Empty
except ImportError as e:
    # Python 2.x
    from Queue import Queue, Empty

def enqueue_output( process, queue ):
    try:
        outs, errs = process.communicate()
    except Exception:
        proc.kill()

class StreamProcess( object ):
    '''
    StreamProcess

https://github.com/kkroening/ffmpeg-python/issues/156#issuecomment-449553709
    '''
    def __init__( self, fname, device = '/dev/video20', verbose = True ):
        super( StreamProcess, self ).__init__()
        self._q = Queue()

        self._verbose = verbose
        if verbose: print( 'Attempting to Stream: {} to {}'.format( fname, device ) )
        width, height, num_frames = probe( fname )
        if verbose: print( '{0}: w={1}, h={2}'.format( fname, width, height ) )

        # Create ffmpeg interface process
        inp = ffmpeg.input( fname, re=None, ).output( device, f='v4l2' )
        if verbose: print( inp.compile() )

        process = (
            inp.run_async( pipe_stdout      = False,#True,
                           pipe_stdin       = False,#True,
                           quiet            = True,
                           overwrite_output = True,
            )
        )
        self._proc = process
        self._t    = Thread(target=enqueue_output, args=(process, self._q ))
        self._t.deamon = True # Thread must die with the program
        self._t.start()


    @property
    def readline( self ):
    #    return self._proc.stdout.readline()
        try:
            line = self._q.get_nowait() # or q.get(timeout=.1)
        except Empty:
            return None
        return line


    def read( self, bufsize = 80 ):
        self._output += self._proc.stdout.read( bufsize )

    @property
    def alive( self ):
        alive = self._proc.poll() == None
        return alive

    def stop( self ):
        self._proc.kill()
        self._t.join()

    def dump( self ):
        for line in self.readline:
            print( line )



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

def test_stream_media( fname, dev = '/dev/video20' ):
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
    pdb.set_trace()
    out, err = process.communicate()

def create_test_src(path='./testsrc.mp4', duration = 30):
    '''
    ffmpeg -f lavfi -i testsrc -t 30 -pix_fmt yuv420p testsrc.m4p
    '''
    process = (
        ffmpeg
        .input( 'testsrc', f='lavfi', t= duration  )
        .output( path, pix_fmt='yuv420p' )
        .run_async( pipe_stdout = True, pipe_stdin = False)
        )
    out, err = process.communicate()

# Main
def main():
    print( "hello" )
    testsrc = './testsrc.mp4'
    test_stream_media( testsrc )


# Standard biolerplate to call the main() function to begin the program
if __name__ == '__main__':
    main()
