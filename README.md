using vagrant and virtualbox to keep our dev environment consistent.


preposition
===

. [virtualbox-4.3.26](http://download.virtualbox.org/virtualbox/4.3.26/VirtualBox-4.3.26-98988-OSX.dmg)
. [vagrant-1.72.](https://dl.bintray.com/mitchellh/vagrant/vagrant_1.7.2.dmg)


cmd helps
===


init vm
====

initial environment, using an exist virtualbox image to create a virtual machine, and save that virutal
machine related resources at working directory. and it will create a vagrant folder beside the vm under
the same directory.

    gmei init --vbox /path/to/vbox --working /path/to/working/dir

vbox should use the prepared one, with required tools, packages installed


manage vm
====

start, stop and ssh into virtual machine

    gmei vm start|stop|ssh
