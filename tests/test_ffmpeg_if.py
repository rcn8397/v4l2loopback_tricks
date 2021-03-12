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
        outpath = '{}_{}.jpg'.format( 'preview', i )
        print( 'Generating preview {} @ {} seconds: {}'.format( step, outpath, ts ) )
        ffmpeg_if.generate_thumbnail( m , outpath, time = ts )

def test_probe():
    print( ffmpeg_if.probe( m ) )
    print( ffmpeg_if.probe_duration( m ) )
    
def main():
    test_probe()
    test_thumbnail()
    
if __name__ == '__main__':
    main()
