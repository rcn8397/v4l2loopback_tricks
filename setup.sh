
if [[ "$OSTYPE" != "linux-gnu"* ]]; then
    echo "Requires Ubuntu linux"
    exit 1
fi

function install_package(){
    PKG_OK=$(dpkg-query -W --showformat='${Status}\n' $1|grep "install ok installed")
    echo Checking for $1: $PKG_OK
    if [ "" = "$PKG_OK" ]; then
        echo "No $1. Setting up $1."
        sudo apt-get --yes install $1
    fi
}

echo "Installing OS dependencies"
install_package v4l2loopback-dkm
install_package v4l2loopback-utils
install_package ffmpeg
#install_package python3-pyqt5

echo "Install Python dependencies"
python3 -m pip install ffmpeg-python
python3 -m pip install pyqt5

echo "Setting up video loopback"
echo options v4l2loopback devices=1 video_nr=20 \
card_label="X920" exclusive_caps=1 | sudo tee -a \
/etc/modprobe.d/virtualcam.conf

echo v4l2loopback | sudo tee -a /etc/modules-load.d/virtualcam.conf

sudo modprobe -r v4l2loopback
sudo modprobe v4l2loopback
