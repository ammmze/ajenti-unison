import os
import glob
import fileinput
import logging
import re
from ajenti.api import *
from ajenti.utils import *
from ajenti.com import *
from ajenti.standalone import make_log
from subprocess import Popen, PIPE
 
 
class Profile:
    filename    = ''
    name        = ''
    params      = []

    log = make_log(debug=True)

    def __init__(self, config, filename = None):
        self.config     = config
        if filename is not None:
            self.load(filename)

    def load(self, filename):
        self.filename   = filename
        self.name       = self.parse_name(filename)
        self.parse_file()

    def save(self):
        self.config.save(self)

    def set_param(self, key, value, index = None):
        p = self.blank_param()
        p['key'] = key
        p['value'] = value
        if index is not None and self.params[index] is not None:
            self.params[index] = p
        else:
            self.params.append(p)

    def get_params(self, key):
        p = []
        for param in self.params:
            if param['key'] == key:
                p.append(param)

        return p

    def get_root1(self):
        p = self.get_params('root')
        try:
            if p[0] is not None:
                root = p[0]['value']
        except IndexError:
            root = ''
        return root

    def set_root1(self, val):
        p = self.get_params('root')
        i = self.params.index(p[0])
        self.set_param('root', val, i)

    def get_root2(self):
        p = self.get_params('root')
        try:
            if p[1] is not None:
                root = p[1]['value']
        except IndexError:
            root = ''
        return root

    def set_root2(self, val):
        p = self.get_params('root')
        i = self.params.index(p[1])
        self.set_param('root', val, i)

    def parse_name(self, filename):
        # Split name of the file into parts based on extenstion separator
        nameParts = os.path.basename(filename).split(os.extsep)

        # Remove the last part of the array (the extension)
        nameParts.pop()

        # Join them back together
        return os.extsep.join(nameParts)

    def parse_file(self):
        self.params = []
        lines = self.config.read(self)
        for line in lines:
            l       = line.strip()
            parts   = l.split('=', 1)
            if (len(parts) == 2):
                key     = parts[0].strip()
                value   = parts[1].strip()
                self.params.append({'key':key,'value':value})

    def to_file(self):
        f = ''
        for p in self.params:
            f = f + p['key'] + ' = ' + p['value'] + '\n'
        return f

    def blank_param(self):
        return {'key':'','value':''}

    def start(self):
        name = self.socket_name()
        p1 = Popen(["screen","-Amd", "-S", name, "nice", "unison", self.name, "-auto", "-batch"])
        p1.communicate()
        # screen -Amd -S name nice unison self.name -auto -batch
        return None

    def stop(self):
        if self.is_running():
            pid = self.get_pid()
            p1 = Popen(["kill",pid])
            p1.communicate()
            print pid
        return None

    def get_pid(self):
        s = self.screen_socket()
        if s is not None:
            result = re.match("^[0-9]+", s)
            if result is not None:
                return result.group(0)
        return None

    def is_running(self):
        if self.screen_socket() is not None:
            return True
        return False

    def get_status(self):
        status = "Not Running"
        if self.is_running():
            status = "Running"
            # Looking for changes
            # Reconciling changes
        return status

    def screen_socket(self):
        # screen -ls | grep -wo '\([0-9]\+\).unison-profile-mediasync'
        p1 = Popen(["screen","-ls"], stdout=PIPE)
        p2 = Popen(["grep","-wo","\([0-9]\+\)."+self.socket_name()+""], stdin=p1.stdout, stdout=PIPE)
        p1.stdout.close()
        output = p2.communicate()[0]
        
        if p2.returncode == 0:
            return output

        return None

    def socket_name(self):
        return 'unison-profile-' + self.name

 
 
class Config(Plugin):
    implements(IConfigurable)
    name = 'Unison'
    icon = '/dl/unison/icon.png'
    id = 'unison'
    config_path = os.path.expanduser("~/.unison")
 
    def list_files(self):
        return [self.config_path + '/*.prf']
    
    def read_profiles(self):
        p = []
        pattern = self.config_path + '/*.prf'

        if os.path.exists(self.config_path):
            for filename in glob.iglob(pattern):
                profile = Profile(self, filename)
                p.append(profile)

        return p

    def read(self, profile):
        return ConfManager.get().load('unison', profile.filename).split('\n')
 
    def save(self, profile):
        ConfManager.get().save('unison', profile.filename, profile.to_file())
        ConfManager.get().commit('unison')