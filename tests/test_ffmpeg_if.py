import os
import sys
import pdb

# Add the project root to the path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from v4l2tricks import ffmpeg_if
        
m = './testsrc.mp4'

def test_thumbnail():
    duration = ffmpeg_if.probe_duration( m )
    print( 'duration: {}'.format( duration ) )
    timestamp = lambda duration, step: ( ( duration/step ) - ( 0.5 * ( duration * 0.25 ) ) )

    # Make 4 thumbnails for previewing
    for i in range( 4, 0, -1 ):
        step = 5 - i
        ts = timestamp( duration, step )
        outpath = '{}_{:03}.jpg'.format( 'preview', i )
        print( 'Generating preview {} @ {} seconds: {}'.format( step, outpath, ts ) )
        ffmpeg_if.generate_thumbnail( m , outpath, time = ts )

    ffmpeg_if.jpgs2gif( 'preview_%03d.jpg' )

def test_gif():
    print( 'Generating gif' )
    duration = ffmpeg_if.probe_duration( m )
    print( 'duration: {}'.format( duration ) )
    timestamp = lambda duration, step: ( ( duration/step ) - ( 0.5 * ( duration * 0.25 ) ) )

    ffmpeg_if.generate_gif( m, 'test.gif', time = timestamp( duration, 3 ), duration =3 )
    
def test_probe():
    print( ffmpeg_if.probe( m ) )
    print( ffmpeg_if.probe_duration( m ) )

    
def main():
    test_probe()
    test_thumbnail()
    test_gif()
    
if __name__ == '__main__':
    main()
