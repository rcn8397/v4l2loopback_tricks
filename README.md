# v4l2loopback_tricks
v4l2loopback tricks

# Tricks/Tools based around the v4l2loopback kernel module
https://github.com/umlaeute/v4l2loopback

# Setup
Hard requirement for v4l2loopback kernel module and ffmpeg

## Python modules
    pip install ffmpeg-python
    pip install PyQt5 (if using the gui.py)
    
## v4l2loopback
### Ubuntu/Debian install:
    sudo apt install v4l2loopback-dkms

### Configure the kernel module
   
    echo options v4l2loopback devices=1 video_nr=20 \
    card_label="X920" exclusive_caps=1 | sudo tee -a \
    /etc/modprobe.d/virtualcam.conf

    echo v4l2loopback | sudo tee -a /etc/modules-load.d/virtualcam.conf

    sudo modprobe -r v4l2loopback
    sudo modprobe v4l2loopback

## ffmpeg
### Ubuntu/Debian install
    sudo apt-get install ffmpeg

### Test video source
From stackoverflow: https://stackoverflow.com/questions/11640458/how-can-i-generate-a-video-file-directly-from-an-ffmpeg-filter-with-no-actual-in
Generated from ffmpeg by:

    ffmpeg -f lavfi -i testsrc -t 30 -pix_fmt yuv420p testsrc.mp4

or

    python ./scripts/mktstsrc.py

