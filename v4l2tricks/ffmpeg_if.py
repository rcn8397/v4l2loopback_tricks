#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""ffmpeg interfaces
"""
import os
import sys
import ffmpeg
from threading import Thread

buffersize = 1024


try:
    from queue import Queue, Empty
except ImportError as e:
    # Python 2.x
    from Queue import Queue, Empty

def queue_stdout( process, queue ):
    print( 'queuing stdout' )
    while process.poll() is None:
        buf = process.stdout.read( buffersize )
        queue.put( buf )
    print('closing stdout' )
    process.stdout.close()

def queue_stderr( process, queue ):
    print( 'queuing stderr' )
    while process.poll() is None:
        try:
            queue.put( process.stderr.next() )
        except StopIteration as e:
            print( 'stop iteration' )
            pass
    print('closing stdout' )
    process.stdout.close()

def process_communicate( process, queue ):
    out, err = process.communicate()


class StreamProcess( object ):
    '''
    StreamProcess

    https://github.com/kkroening/ffmpeg-python/issues/156#issuecomment-449553709

    Should '-hwaccel vdpau' be set?
    '''
    def __init__( self, fname, device = '/dev/video20', sink = False, verbose = True ):
        super( StreamProcess, self ).__init__()
        self._stdout_q = Queue()
        self._stderr_q = Queue()
        self._verbose = verbose
        if verbose: print( 'Attempting to Stream: {} to {}'.format( fname, device ) )
        width, height, num_frames = probe( fname )
        if verbose: print( '{0}: w={1}, h={2}'.format( fname, width, height ) )

        # Create ffmpeg interface process
        stream = ffmpeg.input( fname, re=None, ).output( device, f='v4l2' )
        if verbose: print( stream.compile() )


        process = (
            stream.run_async( pipe_stdout      = not sink,#False,#True,
                              pipe_stdin       = not sink,#False,#True,
                              quiet            = True,
                              overwrite_output = True,
            )
        )
        self._proc = process
        if not sink:
            print( 'threading io')
            self.thread_io()
        else:
            print( 'sink' )
            self.process_sink()


    def process_sink( self ):
        self._stdout_t = Thread( target=process_communicate, args = (self._proc, None))
        self._stdout_t.deamon = True
        self._stdout_t.start()
        self._stderr_t = None

    def thread_io( self ):
        self._stdout_t = Thread( target=queue_stdout, args=( self._proc, self._stdout_q ) )

        self._stderr_t = Thread( target=queue_stderr, args=( self._proc, self._stderr_q ) )
        # Threads must die with the program
        self._stdout_t.deamon = True
        self._stderr_t.deamon = True

        # Start the threads
        self._stdout_t.start()
        self._stderr_t.start()


    @property
    def readline( self ):
    #    return self._proc.stdout.readline()
        try:
            line = self._stderr_q.get(timeout=0.1)#_nowait() # or q.get(timeout=.1)
        except Empty:
            return None
        return line

    @property
    def alive( self ):
        alive = self._proc.poll() == None
        return alive

    def stop( self ):
        self._proc.kill()
        self._stdout_t.join()
        if self._stderr_t is not None:
            self._stderr_t.join()
            self._proc.stderr.close()
        self._proc.stdout.close()
        
        


class OverlayStreamProcess( StreamProcess ):
    def __init__( self, fname, overlay, device = '/dev/video20', sink = False,  verbose = True ):
        self._stdout_q = Queue()
        self._stderr_q = Queue()
        self._verbose = verbose

        # Create ffmpeg interface process
        print( 'Building up sources' )
        base = ffmpeg.input( fname, re=None )
        logo = ffmpeg.input( overlay )
        print( 'Combining inputs' )
        stream  = (
            ffmpeg
            .filter( [base, logo], 'overlay', 10, 10 )
            .output( device, f='v4l2' )
            )
        if verbose: print( stream.compile() )

        process = (
            stream.run_async( pipe_stdout      = not sink,
                              pipe_stdin       = not sink,
                              quiet            = False,
                              overwrite_output = True,
            )
        )
        self._proc = process
        if not sink:
            self.thread_io()
        else:
            self.process_sink()


class DesktopStreamProcess( StreamProcess ):
    def __init__( self,
                  x,
                  y,
                  w       = 640,
                  h       = 480,
                  display = ':0',
                  device  = '/dev/video20',
                  verbose = True ):
        '''
        Resolutions tested:
        640x480
        720x480
        1280x720

        Note: don't forget to stop VLC before changing resolution

        ffmpeg -f x11grab -s 640x480 -i :0.0+10,20 -vf format=pix_fmts=yuv420p -f v4l2 /dev/video1
        '''
        self._stdout_q = Queue()
        self._stderr_q = Queue()
        self._verbose = verbose

        # Create ffmpeg interface process
        stream = (
        ffmpeg
        .input( '{0}.0+{1},{2}'.format( display, x, y ),
                s='{0}x{1}'.format( w, h ),
                #f='x11grab' ).hflip()
                f='x11grab' )
        .output( device,
                 #vf = 'format=pix_fmts=yuv420p',
                 #pix_fmt='yuv420p',
                 pix_fmt='yuyv422',
                 f='v4l2'  )
        )
        if verbose: print( stream.compile() )

        process = (
            stream.run_async( pipe_stdout      = False,
                              pipe_stdin       = False,
                              quiet            = True,
                              overwrite_output = True,
            )
        )
        self._proc = process
        self.process_sink()

class DesktopScopeProcess( StreamProcess ):
    def __init__( self,
                  x,
                  y,
                  w       = 640,
                  h       = 480,
                  display = ':0',
                  device  = '/dev/video20',
                  verbose = True ):
        '''
        Resolutions tested:
        640x480
        720x480
        1280x720

        Note: don't forget to stop VLC before changing resolution

        ffmpeg -f x11grab -s 640x480 -i :0.0+10,20 -vf format=pix_fmts=yuv420p -f v4l2 /dev/video1
        '''
        self._stdout_q = Queue()
        self._stderr_q = Queue()
        self._verbose = verbose

        # Create ffmpeg interface process
        stream = (
        ffmpeg
        .input( '{0}.0+{1},{2}'.format( display, x, y ),
                s='{0}x{1}'.format( w, h ),
                f='x11grab' ).hflip()
        .output( device,
                 pix_fmt='yuyv422',
                 f='v4l2'  )
        )
        if verbose: print( stream.compile() )

        process = (
            stream.run_async( pipe_stdout      = True,
                              pipe_stdin       = True,
                              quiet            = False,
                              overwrite_output = False,
            )
        )
        self._proc = process
        self.process_sink()

        
def jpgs2gif( pattern, out='out.gif', framerate = 2 ): #scale='360x240', ):
    '''
    ffmpeg -f image2 -framerate 10 -i thumb/%001d.jpg -vf scale=480x240  out.gif

    setting framerate to a larger number increases animation speed
    scale is working but things aren't correct
    '''
    out, err = (
        ffmpeg
        .input( pattern, framerate=framerate, format='image2' )
        #.filter( 'scale', scale )
        .output( out)
        .overwrite_output()
        .run( capture_stdout = False )
        )
    return out
    
        
def generate_thumbnail(in_filename, out_filename, time=0.1, width=360):
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
        print( 'borked' )
        return (str( e ) )#e.stderr.decode(), file=sys.stderr)

def probe_duration( fname ):
    '''
    Retrieve the media files duration
    '''
    probe = ffmpeg.probe(fname)
    video_info = next(s for s in probe['streams'] if s['codec_type'] == 'video')
    return( float(video_info['duration']) )
    
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

def create_sine_src(path='./sinewav.mp4', freq = 1000, duration = 5 ):
    '''
    '''
    src = "sine=frequency={}:duration={}".format( freq, duration )
    process=(
        ffmpeg
        .input( src, f='lavfi' )
        .output( path )
        .run_async( pipe_stdout = True, pipe_stdin = False )
        .overwrite_ouput()
        )
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
    testsrc = './testsrc.mp4'
    sinesrc = './sinesrc.mp4'
    create_sine_src( sinesrc )
    test_stream_media( sinesrc )


# Standard biolerplate to call the main() function to begin the program
if __name__ == '__main__':
    main()
