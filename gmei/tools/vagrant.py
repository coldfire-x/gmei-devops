#! -*- coding: utf8 -*-

import os
import sys
import subprocess
import ConfigParser
from functools import wraps

import gmei
from gmei.utils import confirm, alert, green, red


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

    # config directory
    config_dir = os.path.expanduser('~/.gmei')
    # default configuration file, create this after init a box
    config_path = os.path.join(config_dir, 'gmei.ini')

    salt_dir = os.path.join(config_dir, 'salt')
    salt_repo = 'git@github.com:pengfei-xue/gmei-salt.git'

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

        create vagrant file, config directory, write configs into user's home
        directory, and finally create a virtual machine.
        """
        self._create_config_dir()
        self._create_working_directory()
        self._create_salt_repo()
        self._create_vagrant_file()
        self._init_vagrant_box()

    def _create_salt_repo(self):
        """clone gmei-salt into ~/.gmei/salt."""
        green('==> Clone salt repo')

        if os.path.exists(self.salt_dir):
            return

        cmd = 'git clone %s %s' % (self.salt_repo, self.salt_dir)
        subprocess.check_call(cmd.split())

    def _update_salt_repo(self):
        """update salt repo."""
        cmd = 'git -C %s pull' % self.salt_dir
        subprocess.check_call(cmd.split())

    def _create_config_dir(self):
        """create config directory ~/.gmei ."""
        green('==> create configuration directory %s' % self.config_dir)

        if os.path.exists(self.config_dir):
            return

        os.makedirs(self.config_dir)

    def _create_working_directory(self):
        green('==> create working space %s' % self.wk_dir)

        if not os.path.exists(self.wk_dir):
            ok = confirm('create directory %s' % self.wk_dir)
            if not ok:
                sys.exit()

            try:
                os.makedirs(self.wk_dir)
            except Exception as e:
                alert('==> create working directory %s failed!' % self.wk_dir)
                print e
                sys.exit()

    def _create_vagrant_file(self):
        """create vagrant file in separate directory."""
        path = os.path.join(self.wk_dir, 'vagrant')
        green('==> creating vagrant folder %s' % path)

        if not os.path.exists(path):
            os.mkdir(path)

        tmpl = self._vagrant_template()
        minion_conf = os.path.join(self.salt_dir, 'minion-dev')
        salt_roots = os.path.join(self.salt_dir, 'roots')
        vagrantfile = tmpl % (self.box_name, self.wk_dir, salt_roots, minion_conf)
        self.vagrantfile_path = os.path.join(path, 'Vagrantfile')
        with open(self.vagrantfile_path, 'w') as f:
            f.write(vagrantfile)

    def _init_vagrant_box(self):
        if not os.path.exists(self.vbox):
            alert('==> %s does not exist!')
            sys.exit()

        current_dir = os.path.abspath(os.curdir)
        os.chdir(os.path.dirname(self.vagrantfile_path))

        cmd = 'box add %s %s --force' % (self.box_name, self.vbox)
        self._call(cmd)
        self._call('up --provision')

        os.chdir(current_dir)

    def _write_configs(self):
        self.configer.set('vagrantfile', os.path.dirname(self.vagrantfile_path))
        self.configer.set('box', self.box_name)
        self.configer.set('salt', self.salt_dir)

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
                print e
                sys.exit()

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
        ok = confirm('shutdown your virtual machine first')
        if not ok:
            red('==> abort upgrade')
            return

        self.down()
        self._update_salt_repo()
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
  config.vm.synced_folder "%s", "/opt/services"

  config.ssh.forward_agent = true

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
  config.vm.provision :salt do |salt|
    salt.minion_config = "%s"
    salt.run_highstate = true
    salt.verbose = true
  end
end
'''
