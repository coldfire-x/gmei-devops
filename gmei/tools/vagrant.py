#! -*- coding: utf8 -*-

import os
import sys
import subprocess
import ConfigParser
from functools import wraps

import gmei
from gmei.utils import confirm, alert, green


class _VagrantConfig(object):
    """vagrant related configs."""

    section = 'vagrant'

    def __init__(self, config_path):
        self.config_path = config_path
        self._cp = ConfigParser.ConfigParser()

    def _has_section(self):
        if not os.path.exists(self.config_path):
            return

        self._cp.read(self.config_path)
        return self.section in self._cp.sections()

    def get(self, key):
        if not self._has_section():
            return

        self._cp.read(self.config_path)
        return self._cp.get(self.section, key)

    def set(self, key, value):
        has_section = False
        if self._has_section():
            has_section = True

        with open(self.config_path, 'w') as f:
            if not has_section:
                self._cp.add_section(self.section)
            self._cp.set(self.section, key, value)
            self._cp.write(f)


class Vagrant(object):
    """vagrant command wrapper."""

    # vagrant executable
    bin = '/usr/bin/vagrant'

    box_name = 'gmei-box'

    # default configuration file, create this after init a box
    config_path = os.path.expanduser('~/.gmei.ini')

    def vagrant_env_wrapper(f):
        """vagrant execution environment wrapper."""
        @wraps(f)
        def wrapper(self, *args, **kwargs):
            current_dir = os.path.abspath(os.curdir)
            os.chdir(self.configer.get('vagrantfile'))
            f(self, *args, **kwargs)
            os.chdir(current_dir)
        return wrapper

    def __init__(self):
        # set default configuration file location
        self.configer = _VagrantConfig(self.config_path)

    def init(self, vbox, wk_dir):
        self.vbox = vbox
        self.wk_dir = wk_dir

        self._init()

        # init vm successfully, write related configs to ~/.gmei.ini
        self._write_configs()

    def _init(self):
        """init vagrant environment.

        create vagrant file, write configs into user's home directory, and finally
        create a virtual machine.
        """
        self._create_working_directory()
        self._create_vagrant_file()
        self._init_vagrant_box()

    def _create_working_directory(self):
        if not os.path.exists(self.vbox):
            alert('%s does not exist!')
            sys.exit(1)

        if not os.path.exists(self.wk_dir):
            ok = confirm('create directory %s' % self.wk_dir)
            if not ok:
                sys.exit(1)

            try:
                os.makedirs(self.wk_dir)
            except Exception as e:
                alert('create working directory %s failed!' % self.wk_dir)
                print e
                sys.exit(1)

    def _create_vagrant_file(self):
        path = os.path.join(self.wk_dir, 'vagrant')
        print '==> creating vagrant folder %s' % path
        if not os.path.exists(path):
            os.mkdir(path)

        tmpl = self._vagrant_template()
        vagrantfile = tmpl % (self.box_name, self.wk_dir)
        self.vagrantfile_path = os.path.join(path, 'Vagrantfile')
        with open(self.vagrantfile_path, 'w') as f:
            f.write(vagrantfile)

    def _init_vagrant_box(self):
        current_dir = os.path.abspath(os.curdir)
        os.chdir(os.path.dirname(self.vagrantfile_path))

        cmd = '%s box add %s %s --force' % (self.bin, self.box_name, self.vbox)
        subprocess.check_call(cmd.split())

        cmd = '%s up' % self.bin
        subprocess.check_call(cmd.split())

        os.chdir(current_dir)

    def _write_configs(self):
        self.configer.set('vagrantfile', os.path.dirname(self.vagrantfile_path))
        self.configer.set('box', self.box_name)

    def _vagrant_template(self):
        return VAGRANT_TEMPLATE

    def _call(self, cmd, slient=False):
        """vagrant cmd call wiht subprocess.check_call."""
        cmd = '%s %s' % (self.bin, cmd)
        green('==> Running %s' % cmd)

        try:
            subprocess.check_call(cmd.split())
        except Exception as e:
            if not slient:
                alert(e.child_traceback)

    @vagrant_env_wrapper
    def ssh(self):
        self._call('ssh', True)

    @vagrant_env_wrapper
    def up(self):
        self._call('up')

    @vagrant_env_wrapper
    def down(self):
        self._call('halt')

    @vagrant_env_wrapper
    def update(self):
        self._call('up --provision')


VAGRANT_TEMPLATE = '''
# -*- mode: ruby -*-
# vi: set ft=ruby :

# All Vagrant configuration is done below. The "2" in Vagrant.configure
# configures the configuration version (we support older styles for
# backwards compatibility). Please don't change it unless you know what
# you're doing.
Vagrant.configure(2) do |config|
  # The most common configuration options are documented and commented below.
  # For a complete reference, please see the online documentation at
  # https://docs.vagrantup.com.

  # Every Vagrant development environment requires a box. You can search for
  # boxes at https://atlas.hashicorp.com/search.
  config.vm.box = "%s"

  # Disable automatic box update checking. If you disable this, then
  # boxes will only be checked for updates when the user runs
  # `vagrant box outdated`. This is not recommended.
  config.vm.box_check_update = false

  # Create a forwarded port mapping which allows access to a specific port
  # within the machine from a port on the host machine. In the example below,
  # accessing "localhost:8080" will access port 80 on the guest machine.
  # config.vm.network "forwarded_port", guest: 80, host: 8080

  # Create a private network, which allows host-only access to the machine
  # using a specific IP.
  config.vm.network :private_network, ip: "10.11.12.13"

  # Create a public network, which generally matched to bridged network.
  # Bridged networks make the machine appear as another physical device on
  # your network.
  # config.vm.network "public_network"

  # Share an additional folder to the guest VM. The first argument is
  # the path on the host to the actual folder. The second argument is
  # the path on the guest to mount the folder. And the optional third
  # argument is a set of non-required options.
  config.vm.synced_folder "%s", "/workspace/"

  # Provider-specific configuration so you can fine-tune various
  # backing providers for Vagrant. These expose provider-specific options.
  # Example for VirtualBox:
  #
  config.vm.provider "virtualbox" do |vb|
    # Display the VirtualBox GUI when booting the machine
    vb.gui = false

    # Customize the amount of memory on the VM:
    vb.memory = "2048"

    vb.name = "gengmei-box"
  end
  #
  # View the documentation for the provider you are using for more
  # information on available options.

  # Enable provisioning with a shell script. Additional provisioners such as
  # Puppet, Chef, Ansible, Salt, and Docker are also available. Please see the
  # documentation for more information about their specific syntax and use.
  # config.vm.provision "shell", inline: <<-SHELL
  #   sudo apt-get update
  #   sudo apt-get install -y apache2
  # SHELL
end
'''
