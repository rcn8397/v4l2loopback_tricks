import os
import sys

# Add the project root to the path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from v4l2tricks import ffmpeg_if
        

def test_probe():
    m = './testsrc.mp4'
    print( ffmpeg_if.probe( m ) )
    print( ffmpeg_if.probe_duration( m ) )
    
def main():
    test_probe()

if __name__ == '__main__':
    main()
