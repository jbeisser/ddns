#!/usr/bin/env python

import os
import sys
import subprocess as sp
import time
import urllib2
from optparse import OptionParser


# static VARS
DDNS_HOST = "members.dyndns.org"
DDNS_URL  = "/nic/update"

# gotta rewrite this
class updater_t(object):
    def __init__(self, user=None, pw=None, iface=None, dfile=None, hosts=None, domain=None):
        #socket.setdefaulttimeout(2)
        self.url    = None
        self.user   = user
        self.pw     = pw
        self.iface  = iface
        self.dfile  = dfile
        self.hosts  = hosts
        self.domain = domain
        self.UA     = "Slightly Less Than Simple DynDNS Updater; Python/urllib2 - 0.1"


    def update(self):
        passm = urllib2.HTTPPasswordMgrWithDefaultRealm()
        passm.add_password(None, 'https://%s' % DDNS_HOST, self.user, self.pw)
        handler = urllib2.HTTPBasicAuthHandler(passm)
        opener = urllib2.build_opener(handler)
        urllib2.install_opener(opener)

        req = urllib2.Request(self.buildURL(), headers={'User-Agent':self.UA})
        res = urllib2.urlopen(req)

        print(res.read())
        #return self.parse(res.read())


    def buildURL(self):
        base  = 'https://' + DDNS_HOST + DDNS_URL
        hosts = self.buildHostnames(self.hosts)
        ip    = self.iface.getIP()

        h = "hostname=%s&" % hosts
        i = "myip=%s&" % ip

        url = base + '?' + h + i

        return url


    def buildHostnames(self, hosts):
        l = []
        for h in hosts:
            l.append("%s.%s" % (h.strip(), self.domain))
        return ','.join(l)


    def parse(self, res):
        '''parse the answer to figure out success or not.'''
        if res.startswith() is 'good':
            sys.exit()
        elif res is 'nochg':
            sys.exit('nochg: update unneccassary')
        else:
            raise(res)



class interface_t(object):
    def __init__(self, iface=None):
        self.iface = iface
        self.IP = None
        self.getIP()


    def getIP(self):
        if self.IP == None:
            cmd = ["/sbin/ifconfig", self.iface, "inet"]
            s = sp.Popen(cmd, stdout=sp.PIPE).communicate()[0]
            for l in s.split('\n\t'):
                if l.startswith('inet'):
                    self.IP = l.split()[1]
        return self.IP


    def getIF(self):
        return self.iface



class file_t(object):
    def __init__(self, fn=None):
        self.fn = fn


    def getFn(self):
        return self.fn


    def setFn(self, fn):
        self.fn = fn


    def exists(self):
        return(os.path.exists(self.fn))



class datafile_t(file_t):
    #def __init__(self, fn='/var/db/dyndns.db'):
    def __init__(self, fn='/tmp/dyndns.db'):
        file_t.__init__(self, fn)
        self.IP    = None
        self.hosts = None


    def read(self):
        ip = None
        hosts = None
        li = []
        fh = open(self.fn, 'r')

        for l in fh.readlines():
            if l.startswith('#'):
                pass
            else:
                li.append(l.strip())
        fh.close()

        if len(li) >= 1:
            self.IP = li[0]
            self.hosts = li[1:]


    def setIP(self, ip):
        self.IP = ip


    def setHosts(self, hosts):
        self.hosts = hosts


    def write(self, ip = None, hosts = None):
        if ip == None:
            ip = self.IP
        if hosts == None:
            hosts = self.hosts
        t = time.asctime()
        tz = time.tzname[time.daylight]
        ts = "# Updated %s %s\n" % (t, tz)

        #assert ip and hosts
        fh = open(self.fn, 'w')
        fh.write(ts)
        fh.write(ip + '\n')
        for h in hosts:
            fh.write(h + '\n')
        fh.close()



class config_t(file_t):
    def __init__(self, fn='/etc/ddns/config'):
        file_t.__init__(self, fn)
        self.fn    = fn
        self.user  = None
        self.pw    = None
        self.dom   = None
        self.hosts = []


    def read(self):
        fh = open(self.fn, 'r')
        for l in fh.readlines():
            if l.startswith('#'):
                pass
            elif l.startswith('user'):
                self.user = l.split('=')[1].strip()
            elif l.startswith('pass'):
                self.pw = l.split('=')[1].strip()
            elif l.startswith('domai'):
                self.dom = l.split('=')[1].strip()
            elif l.startswith('host'):
                self.hosts.append(l.split('=')[1].strip())
            else:
                pass
        fh.close()


    def getUser(self):
        return self.user


    def getPass(self):
        return self.pw


    def getDom(self):
        return self.dom


    def getHosts(self):
        return self.hosts




def main():
    parser = OptionParser()
    parser.add_option("-c", "--config", dest="conf",
                    default="/etc/ddns/config", help="config file")
    parser.add_option("-i", "--iface", dest="iface",
                    help="external interface")
    parser.add_option("-d", "--domain", dest="domain",
                    help="DynDNS domain: domain.tld")
    parser.add_option("-u", "--user", dest="user",
                    help="DynDNS username")
    parser.add_option("-p", "--pass", dest="pw",
                    help="DynDNS password")
    parser.add_option("-D", "--debug", dest="debug", action='store_true',
                    default=False,
                    help="debugging output")

    (opt, args) = parser.parse_args()
    user  = None
    pw    = None
    dom   = None
    hosts = None

    iface = interface_t(opt.iface)
    dfile = datafile_t()
    conf  = config_t(opt.conf)

    if conf.exists():
        conf.read()
    if dfile.exists():
        dfile.read()
    if iface.IP == dfile.IP:
        print "no changes!"
        sys.exit()

    if not conf.getUser and not opt.user:
        sys.exit("This needs a username and password to work.")
    elif opt.user:
        user = opt.user
        pw   = opt.pw
    else:
        user  = conf.getUser()
        pw    = conf.getPass()
        dom   = conf.getDom()
        hosts = conf.getHosts()

    update = updater_t(iface=iface, user=user, pw=pw, hosts=hosts, domain=dom)

    dfile.setIP(iface.IP)
    dfile.setHosts(args)
    dfile.write()

    update.update()


if __name__ == '__main__':
    main()

