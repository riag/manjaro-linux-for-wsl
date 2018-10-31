manjaro-bootstrap
=================

Bootstrap a base Manjaro Linux system from any GNU distro.

Install
=======

    # install -m 755 manjaro-bootstrap.sh /usr/local/bin/manjaro-bootstrap

Examples
=========

Create a base Manjaro distribution in directory 'mymjr' (currently running Manjaro by default):

    # manjaro-bootstrap mymjr
   
The same but use arch x86_64 and a given repository source:

    # manjaro-bootstrap -a x86_64 -r "http://repo.manjaro.org.uk/" mymjr 

Usage
=====

Once the process has finished, chroot to the destination directory (default user: root/root):

    # chroot destination

Note that some packages require some system directories to be mounted. Some of the commands you can try:

    # mount --bind /proc mymjr/proc
    # mount --bind /sys mymjr/sys
    # mount --bind /dev mymjr/dev
    # mount --bind /dev/pts mymjr/dev/pts
    
License
=======

This project is licensed under the terms of the MIT license
