#!/bin/bash

# This script builds the bat *.deb packages from svn and installes them

apt-get update
apt-get -y remove bat bat-extratools bat-extratools-java
apt-get -y autoremove

CWD=/tmp/bat/
cd $CWD

apt -y install git devscripts debhelper zlib1g-dev
git clone https://github.com/armijnhemel/binaryanalysis.git
cd binaryanalysis/src/
debuild -uc -us
if [ $? -ne 0 ]; then
    echo ""
    echo "Error debuild bat !!!"
    echo ""
    exit
fi
cp ../*.deb $CWD
cd $CWD
rm -rf binaryanalysis

dpkg --ignore-depends=python-imaging -i ./*.deb
apt install -y -f
dpkg --ignore-depends=python-imaging -i ./*.deb
##if [ $? -ne 0 ]; then
#   echo ""
#    echo "Error installing packages!!!"
 #   echo ""
#fi

#cd ../
