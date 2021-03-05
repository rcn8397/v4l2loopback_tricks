import os
import sys

# Add the project root to the path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from v4l2tricks import fsutil      
        

def test_filewalker():
    discover = fsutil.discover
    path = '.'
    patterns = ['.mp4' ]
    print( discover( path, patterns ) )
    path = os.path.expanduser( '~/Videos' )
    patterns.append( '.gif' )
    print( discover( path, patterns ) )

def main():
    test_filewalker()

if __name__ == '__main__':
    main()
