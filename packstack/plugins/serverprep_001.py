# -*- coding: utf-8 -*-
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
Plugin responsible for Server Preparation.
"""

import os
import re
import logging
import platform

from packstack.installer import exceptions
from packstack.installer import utils
from packstack.installer import validators

from packstack.modules.common import filtered_hosts
from packstack.modules.common import is_all_in_one

# ------------ Server Preparation Packstack Plugin Initialization -------------

PLUGIN_NAME = "OS-SERVERPREPARE"
PLUGIN_NAME_COLORED = utils.color_text(PLUGIN_NAME, 'blue')


def initConfig(controller):
    conf_params = {
        "SERVERPREPARE": [
            {"CMD_OPTION": "use-epel",
             "USAGE": "To subscribe each server to EPEL enter \"y\"",
             "PROMPT": "To subscribe each server to EPEL enter \"y\"",
             "OPTION_LIST": ["y", "n"],
             "VALIDATORS": [validators.validate_options],
             "DEFAULT_VALUE": "n",
             "MASK_INPUT": False,
             "LOOSE_VALIDATION": True,
             "CONF_NAME": "CONFIG_USE_EPEL",
             "USE_DEFAULT": False,
             "NEED_CONFIRM": False,
             "CONDITION": False},

            {"CMD_OPTION": "additional-repo",
             "USAGE": ("A comma separated list of URLs to any additional yum "
                       "repositories to install"),
             "PROMPT": ("Enter a comma separated list of URLs to any "
                        "additional yum repositories to install"),
             "OPTION_LIST": [],
             "DEFAULT_VALUE": "",
             "MASK_INPUT": False,
             "LOOSE_VALIDATION": True,
             "CONF_NAME": "CONFIG_REPO",
             "USE_DEFAULT": False,
             "NEED_CONFIRM": False,
             "CONDITION": False}
        ],

        "RHEL": [
            {"CMD_OPTION": "rh-username",
             "USAGE": ("To subscribe each server with Red Hat subscription "
                       "manager, include this with CONFIG_RH_PW"),
             "PROMPT": "To subscribe each server to Red Hat enter a username ",
             "OPTION_LIST": [],
             "DEFAULT_VALUE": "",
             "MASK_INPUT": False,
             "LOOSE_VALIDATION": True,
             "CONF_NAME": "CONFIG_RH_USER",
             "USE_DEFAULT": False,
             "NEED_CONFIRM": False,
             "CONDITION": False},

            {"CMD_OPTION": "rhn-satellite-server",
             "USAGE": ("To subscribe each server with RHN Satellite,fill "
                       "Satellite's URL here. Note that either satellite's "
                       "username/password or activation key has "
                       "to be provided"),
             "PROMPT": ("To subscribe each server with RHN Satellite enter "
                        "RHN Satellite server URL"),
             "OPTION_LIST": [],
             "DEFAULT_VALUE": "",
             "MASK_INPUT": False,
             "LOOSE_VALIDATION": False,
             "CONF_NAME": "CONFIG_SATELLITE_URL",
             "USE_DEFAULT": False,
             "NEED_CONFIRM": False,
             "CONDITION": False}
        ],

        "RHSM": [
            {"CMD_OPTION": "rh-password",
             "USAGE": ("To subscribe each server with Red Hat subscription "
                       "manager, include this with CONFIG_RH_USER"),
             "PROMPT": ("To subscribe each server to Red Hat enter your "
                        "password"),
             "OPTION_LIST": [],
             "DEFAULT_VALUE": "",
             "MASK_INPUT": True,
             "LOOSE_VALIDATION": True,
             "CONF_NAME": "CONFIG_RH_PW",
             "USE_DEFAULT": False,
             "NEED_CONFIRM": False,
             "CONDITION": False},

            {"CMD_OPTION": "rh-enable-optional",
             "USAGE": "To enable RHEL optional repos use value \"y\"",
             "PROMPT": "To enable RHEL optional repos use value \"y\"",
             "OPTION_LIST": ["y", "n"],
             "VALIDATORS": [validators.validate_options],
             "DEFAULT_VALUE": "y",
             "MASK_INPUT": False,
             "LOOSE_VALIDATION": True,
             "CONF_NAME": "CONFIG_RH_OPTIONAL",
             "USE_DEFAULT": False,
             "NEED_CONFIRM": False,
             "CONDITION": False},

            {"CMD_OPTION": "rh-proxy-host",
             "USAGE": ("Specify a HTTP proxy to use with Red Hat subscription "
                       "manager"),
             "PROMPT": ("Specify a HTTP proxy to use with Red Hat subscription"
                        " manager"),
             "OPTION_LIST": [],
             "DEFAULT_VALUE": "",
             "MASK_INPUT": True,
             "LOOSE_VALIDATION": False,
             "CONF_NAME": "CONFIG_RH_PROXY",
             "USE_DEFAULT": False,
             "NEED_CONFIRM": False,
             "CONDITION": False}
        ],

        "RHSM_PROXY": [
            {"CMD_OPTION": "rh-proxy-port",
             "USAGE": ("Specify port of Red Hat subscription manager HTTP "
                       "proxy"),
             "PROMPT": ("Specify port of Red Hat subscription manager HTTP "
                        "proxy"),
             "OPTION_LIST": [],
             "DEFAULT_VALUE": "",
             "MASK_INPUT": False,
             "LOOSE_VALIDATION": False,
             "CONF_NAME": "CONFIG_RH_PROXY_PORT",
             "USE_DEFAULT": False,
             "NEED_CONFIRM": False,
             "CONDITION": False},

            {"CMD_OPTION": "rh-proxy-user",
             "USAGE": ("Specify a username to use with Red Hat subscription "
                       "manager HTTP proxy"),
             "PROMPT": ("Specify a username to use with Red Hat subscription "
                        "manager HTTP proxy"),
             "OPTION_LIST": [],
             "DEFAULT_VALUE": "",
             "MASK_INPUT": True,
             "LOOSE_VALIDATION": False,
             "CONF_NAME": "CONFIG_RH_PROXY_USER",
             "USE_DEFAULT": False,
             "NEED_CONFIRM": False,
             "CONDITION": False},

            {"CMD_OPTION": "rh-proxy-password",
             "USAGE": ("Specify a password to use with Red Hat subscription "
                       "manager HTTP proxy"),
             "PROMPT": ("Specify a password to use with Red Hat subscription "
                        "manager HTTP proxy"),
             "OPTION_LIST": [],
             "DEFAULT_VALUE": "",
             "MASK_INPUT": True,
             "LOOSE_VALIDATION": False,
             "CONF_NAME": "CONFIG_RH_PROXY_PW",
             "USE_DEFAULT": False,
             "NEED_CONFIRM": False,
             "CONDITION": False}
        ],

        "SATELLITE": [
            {"CMD_OPTION": "rhn-satellite-username",
             "USAGE": "Username to access RHN Satellite",
             "PROMPT": ("Enter RHN Satellite username or leave plain if you "
                        "will use activation key instead"),
             "OPTION_LIST": [],
             "DEFAULT_VALUE": "",
             "MASK_INPUT": False,
             "LOOSE_VALIDATION": True,
             "CONF_NAME": "CONFIG_SATELLITE_USER",
             "USE_DEFAULT": False,
             "NEED_CONFIRM": False,
             "CONDITION": False},

            {"CMD_OPTION": "rhn-satellite-password",
             "USAGE": "Password to access RHN Satellite",
             "PROMPT": ("Enter RHN Satellite password or leave plain if you "
                        "will use activation key instead"),
             "OPTION_LIST": [],
             "DEFAULT_VALUE": "",
             "MASK_INPUT": True,
             "LOOSE_VALIDATION": False,
             "CONF_NAME": "CONFIG_SATELLITE_PW",
             "USE_DEFAULT": False,
             "NEED_CONFIRM": False,
             "CONDITION": False},

            {"CMD_OPTION": "rhn-satellite-activation-key",
             "USAGE": "Activation key for subscription to RHN Satellite",
             "PROMPT": ("Enter RHN Satellite activation key or leave plain if "
                        "you used username/password instead"),
             "OPTION_LIST": [],
             "DEFAULT_VALUE": "",
             "MASK_INPUT": True,
             "LOOSE_VALIDATION": False,
             "CONF_NAME": "CONFIG_SATELLITE_AKEY",
             "USE_DEFAULT": False,
             "NEED_CONFIRM": False,
             "CONDITION": False},

            {"CMD_OPTION": "rhn-satellite-cacert",
             "USAGE": "Specify a path or URL to a SSL CA certificate to use",
             "PROMPT": "Specify a path or URL to a SSL CA certificate to use",
             "OPTION_LIST": [],
             "DEFAULT_VALUE": "",
             "MASK_INPUT": True,
             "LOOSE_VALIDATION": False,
             "CONF_NAME": "CONFIG_SATELLITE_CACERT",
             "USE_DEFAULT": False,
             "NEED_CONFIRM": False,
             "CONDITION": False},

            {"CMD_OPTION": "rhn-satellite-profile",
             "USAGE": ("If required specify the profile name that should be "
                       "used as an identifier for the system "
                       "in RHN Satellite"),
             "PROMPT": ("If required specify the profile name that should be "
                        "used as an identifier for the system "
                        "in RHN Satellite"),
             "OPTION_LIST": [],
             "DEFAULT_VALUE": "",
             "MASK_INPUT": True,
             "LOOSE_VALIDATION": False,
             "CONF_NAME": "CONFIG_SATELLITE_PROFILE",
             "USE_DEFAULT": False,
             "NEED_CONFIRM": False,
             "CONDITION": False},

            {"CMD_OPTION": "rhn-satellite-flags",
             "USAGE": ("Comma separated list of flags passed to rhnreg_ks. "
                       "Valid flags are: novirtinfo, norhnsd, nopackages"),
             "PROMPT": ("Enter comma separated list of flags passed "
                        "to rhnreg_ks"),
             "OPTION_LIST": ['novirtinfo', 'norhnsd', 'nopackages'],
             "VALIDATORS": [validators.validate_multi_options],
             "DEFAULT_VALUE": "",
             "MASK_INPUT": True,
             "LOOSE_VALIDATION": False,
             "CONF_NAME": "CONFIG_SATELLITE_FLAGS",
             "USE_DEFAULT": False,
             "NEED_CONFIRM": False,
             "CONDITION": False},

            {"CMD_OPTION": "rhn-satellite-proxy-host",
             "USAGE": "Specify a HTTP proxy to use with RHN Satellite",
             "PROMPT": "Specify a HTTP proxy to use with RHN Satellite",
             "OPTION_LIST": [],
             "DEFAULT_VALUE": "",
             "MASK_INPUT": True,
             "LOOSE_VALIDATION": False,
             "CONF_NAME": "CONFIG_SATELLITE_PROXY",
             "USE_DEFAULT": False,
             "NEED_CONFIRM": False,
             "CONDITION": False}
        ],

        "SATELLITE_PROXY": [
            {"CMD_OPTION": "rhn-satellite-proxy-username",
             "USAGE": ("Specify a username to use with an authenticated "
                       "HTTP proxy"),
             "PROMPT": ("Specify a username to use with an authenticated "
                        "HTTP proxy"),
             "OPTION_LIST": [],
             "DEFAULT_VALUE": "",
             "MASK_INPUT": True,
             "LOOSE_VALIDATION": False,
             "CONF_NAME": "CONFIG_SATELLITE_PROXY_USER",
             "USE_DEFAULT": False,
             "NEED_CONFIRM": False,
             "CONDITION": False},

            {"CMD_OPTION": "rhn-satellite-proxy-password",
             "USAGE": ("Specify a password to use with an authenticated "
                       "HTTP proxy."),
             "PROMPT": ("Specify a password to use with an authenticated "
                        "HTTP proxy."),
             "OPTION_LIST": [],
             "DEFAULT_VALUE": "",
             "MASK_INPUT": True,
             "LOOSE_VALIDATION": False,
             "CONF_NAME": "CONFIG_SATELLITE_PROXY_PW",
             "USE_DEFAULT": False,
             "NEED_CONFIRM": False,
             "CONDITION": False}
        ]
    }

    def filled_rhsm(config):
        return bool(config.get('CONFIG_RH_USER'))

    def filled_rhsm_proxy(config):
        return bool(config.get('CONFIG_RH_PROXY'))

    def filled_satellite(config):
        return bool(config.get('CONFIG_SATELLITE_URL'))

    def filled_satellite_proxy(config):
        return bool(config.get('CONFIG_SATELLITE_PROXY'))

    conf_groups = [
        {"GROUP_NAME": "SERVERPREPARE",
         "DESCRIPTION": "Server Prepare Configs ",
         "PRE_CONDITION": lambda x: 'yes',
         "PRE_CONDITION_MATCH": "yes",
         "POST_CONDITION": False,
         "POST_CONDITION_MATCH": True},
    ]

    config = controller.CONF
    if (is_all_in_one(config) and is_rhel()) or not is_all_in_one(config):
        conf_groups.extend([
            {"GROUP_NAME": "RHEL",
             "DESCRIPTION": "RHEL config",
             "PRE_CONDITION": lambda x: 'yes',
             "PRE_CONDITION_MATCH": "yes",
             "POST_CONDITION": False,
             "POST_CONDITION_MATCH": True},

            {"GROUP_NAME": "RHSM",
             "DESCRIPTION": "RH subscription manager config",
             "PRE_CONDITION": filled_rhsm,
             "PRE_CONDITION_MATCH": True,
             "POST_CONDITION": False,
             "POST_CONDITION_MATCH": True},

            {"GROUP_NAME": "RHSM_PROXY",
             "DESCRIPTION": "RH subscription manager proxy config",
             "PRE_CONDITION": filled_rhsm_proxy,
             "PRE_CONDITION_MATCH": True,
             "POST_CONDITION": False,
             "POST_CONDITION_MATCH": True},

            {"GROUP_NAME": "SATELLITE",
             "DESCRIPTION": "RHN Satellite config",
             "PRE_CONDITION": filled_satellite,
             "PRE_CONDITION_MATCH": True,
             "POST_CONDITION": False,
             "POST_CONDITION_MATCH": True},

            {"GROUP_NAME": "SATELLITE_PROXY",
             "DESCRIPTION": "RHN Satellite proxy config",
             "PRE_CONDITION": filled_satellite_proxy,
             "PRE_CONDITION_MATCH": True,
             "POST_CONDITION": False,
             "POST_CONDITION_MATCH": True}
        ])

    for group in conf_groups:
        params = conf_params[group["GROUP_NAME"]]
        controller.addGroup(group, params)


def initSequences(controller):
    preparesteps = [
        {'title': 'Preparing servers', 'functions': [server_prep]}
    ]
    controller.addSequence("Preparing servers", [], [], preparesteps)


# ------------------------- helper functions -------------------------

def is_rhel():
    return 'Red Hat Enterprise Linux' in platform.linux_distribution()[0]


def run_rhn_reg(host, server_url, username=None, password=None,
                cacert=None, activation_key=None, profile_name=None,
                proxy_host=None, proxy_user=None, proxy_pass=None,
                flags=None):
    """
    Registers given host to given RHN Satellite server. To successfully
    register either activation_key or username/password is required.
    """
    logging.debug('Setting RHN Satellite server: %s.' % locals())

    mask = []
    cmd = ['/usr/sbin/rhnreg_ks']
    server = utils.ScriptRunner(host)

    # check satellite server url
    server_url = (server_url.rstrip('/').endswith('/XMLRPC')
                  and server_url or '%s/XMLRPC' % server_url)
    cmd.extend(['--serverUrl', server_url])

    if activation_key:
        cmd.extend(['--activationkey', activation_key])
    elif username:
        cmd.extend(['--username', username])
        if password:
            cmd.extend(['--password', password])
            mask.append(password)
    else:
        raise exceptions.InstallError('Either RHN Satellite activation '
                                      'key or username/password must '
                                      'be provided.')

    if cacert:
        # use and if required download given certificate
        location = "/etc/sysconfig/rhn/%s" % os.path.basename(cacert)
        if not os.path.isfile(location):
            logging.debug('Downloading cacert from %s.' % server_url)
            wget_cmd = ('ls %(location)s &> /dev/null && echo -n "" || '
                        'wget -nd --no-check-certificate --timeout=30 '
                        '--tries=3 -O "%(location)s" "%(cacert)s"' %
                        locals())
            server.append(wget_cmd)
        cmd.extend(['--sslCACert', location])

    if profile_name:
        cmd.extend(['--profilename', profile_name])
    if proxy_host:
        cmd.extend(['--proxy', proxy_host])
        if proxy_user:
            cmd.extend(['--proxyUser', proxy_user])
            if proxy_pass:
                cmd.extend(['--proxyPassword', proxy_pass])
                mask.append(proxy_pass)

    flags = flags or []
    flags.append('force')
    for i in flags:
        cmd.append('--%s' % i)

    server.append(' '.join(cmd))
    server.append('yum clean metadata')
    server.execute(mask_list=mask)


def run_rhsm_reg(host, username, password, optional=False, proxy_server=None,
                 proxy_port=None, proxy_user=None, proxy_password=None):
    """
    Registers given host to Red Hat Repositories via subscription manager.
    """
    releasever = config['HOST_DETAILS'][host]['release'].split('.')[0]
    server = utils.ScriptRunner(host)

    # configure proxy if it is necessary
    if proxy_server:
        cmd = ('subscription-manager config '
               '--server.proxy_hostname=%(proxy_server)s '
               '--server.proxy_port=%(proxy_port)s')
        if proxy_user:
            cmd += (' --server.proxy_user=%(proxy_user)s '
                    '--server.proxy_password=%(proxy_password)s')
        server.append(cmd % locals())

    # register host
    cmd = ('subscription-manager register --username=\"%s\" '
           '--password=\"%s\" --autosubscribe || true')
    server.append(cmd % (username, password.replace('"', '\\"')))

    # subscribe to required channel
    cmd = ('subscription-manager list --consumed | grep -i openstack || '
           'subscription-manager subscribe --pool %s')
    pool = ("$(subscription-manager list --available"
            " | grep -m1 -A15 'Red Hat Enterprise Linux OpenStack Platform'"
            " | grep -i 'Pool ID:' | awk '{print $3}')")
    server.append(cmd % pool)

    if optional:
        server.append("subscription-manager repos "
                      "--enable rhel-%s-server-optional-rpms" % releasever)
    server.append("subscription-manager repos "
                  "--enable rhel-%s-server-openstack-5.0-rpms" % releasever)

    # mrg channel naming is a big mess
    if releasever == '7':
        mrg_prefix = 'rhel-x86_64-server-7'
    elif releasever == '6':
        mrg_prefix = 'rhel-6-server'
    server.append("subscription-manager repos "
                  "--enable %s-mrg-messaging-2-rpms" % mrg_prefix)

    server.append("yum clean all")
    server.append("rpm -q --whatprovides yum-utils || "
                  "yum install -y yum-utils")
    server.append("yum clean metadata")
    server.execute(mask_list=[password])


def manage_epel(host, config):
    """
    Installs and/or enables EPEL repo if it is required or disables it if it
    is not required.
    """
    if config['HOST_DETAILS'][host]['os'] in ('Fedora', 'Unknown'):
        return

    # yum's $releasever can be non numeric on RHEL, so interpolate here
    releasever = config['HOST_DETAILS'][host]['release'].split('.')[0]
    mirrors = ('https://mirrors.fedoraproject.org/metalink?repo=epel-%s&'
               'arch=$basearch' % releasever)
    server = utils.ScriptRunner(host)
    if config['CONFIG_USE_EPEL'] == 'y':
        server.append('REPOFILE=$(mktemp)')
        server.append('cat /etc/yum.conf > $REPOFILE')
        server.append("echo -e '[packstack-epel]\nname=packstack-epel\n"
                      "enabled=1\nmirrorlist=%(mirrors)s' >> $REPOFILE"
                      % locals())
        server.append('( rpm -q --whatprovides epel-release ||'
                      ' yum install -y --nogpg -c $REPOFILE epel-release ) '
                      '|| true')
        server.append('rm -rf $REPOFILE')
        try:
            server.execute()
        except exceptions.ScriptRuntimeError as ex:
            msg = 'Failed to set EPEL repo on host %s:\n%s' % (host, ex)
            raise exceptions.ScriptRuntimeError(msg)

    # if there's an epel repo explicitly enables or disables it
    # according to: CONFIG_USE_EPEL
    if config['CONFIG_USE_EPEL'] == 'y':
        cmd = 'enable'
        enabled = '(1|True)'
    else:
        cmd = 'disable'
        enabled = '(0|False)'

    server.clear()
    server.append('rpm -q yum-utils || yum -y install yum-utils')
    server.append('yum-config-manager --%(cmd)s epel' % locals())
    rc, out = server.execute()

    # yum-config-manager returns 0 always, but returns current setup
    # if succeeds
    match = re.search('enabled\s*\=\s*%(enabled)s' % locals(), out)
    if match:
        return
    msg = 'Failed to set EPEL repo on host %s:\n'
    if cmd == 'enable':
        # fail in case user wants to have EPEL enabled
        msg += ('RPM file seems to be installed, but appropriate repo file is '
                'probably missing in /etc/yum.repos.d/')
        raise exceptions.ScriptRuntimeError(msg % host)
    else:
        # just warn in case disabling failed which might happen when EPEL repo
        # is not installed at all
        msg += 'This is OK in case you don\'t want EPEL installed and enabled.'
        # TO-DO: fill logger name when logging will be refactored.
        logger = logging.getLogger()
        logger.warn(msg % host)


def manage_rdo(host, config):
    """
    Installs and enables RDO repo on host in case it is installed locally.
    """
    try:
        cmd = "rpm -q rdo-release --qf='%{version}-%{release}.%{arch}\n'"
        rc, out = utils.execute(cmd, use_shell=True)
    except exceptions.ExecuteRuntimeError:
        # RDO repo is not installed, so we don't need to continue
        return
    # We are installing RDO. EPEL is a requirement, so enable it, overriding
    # any configured option
    config['CONFIG_USE_EPEL'] = 'y'

    match = re.match(r'^(?P<version>\w+)\-(?P<release>\d+\.[\d\w]+)\n', out)
    version, release = match.group('version'), match.group('release')
    rdo_url = ("http://rdo.fedorapeople.org/openstack/openstack-%(version)s/"
               "rdo-release-%(version)s-%(release)s.rpm" % locals())

    server = utils.ScriptRunner(host)
    server.append("(rpm -q 'rdo-release-%(version)s' ||"
                  " yum install -y --nogpg %(rdo_url)s) || true"
                  % locals())
    try:
        server.execute()
    except exceptions.ScriptRuntimeError as ex:
        msg = 'Failed to set RDO repo on host %s:\n%s' % (host, ex)
        raise exceptions.ScriptRuntimeError(msg)

    reponame = 'openstack-%s' % version
    server.clear()
    server.append('yum-config-manager --enable %(reponame)s' % locals())
    # yum-config-manager returns 0 always, but returns current setup
    # if succeeds
    rc, out = server.execute()
    match = re.search('enabled\s*=\s*(1|True)', out)
    if not match:
        msg = ('Failed to set RDO repo on host %s:\nRPM file seems to be '
               'installed, but appropriate repo file is probably missing '
               'in /etc/yum.repos.d/' % host)
        raise exceptions.ScriptRuntimeError(msg)


# -------------------------- step functions --------------------------

def server_prep(config, messages):
    rh_username = None
    sat_url = None
    if is_rhel():
        rh_username = config.get("CONFIG_RH_USER")
        rh_password = config.get("CONFIG_RH_PW")

        sat_registered = set()

        sat_url = config["CONFIG_SATELLITE_URL"].strip()
        if sat_url:
            flag_list = config["CONFIG_SATELLITE_FLAGS"].split(',')
            sat_flags = [i.strip() for i in flag_list if i.strip()]
            sat_proxy_user = config.get("CONFIG_SATELLITE_PROXY_USER", '')
            sat_proxy_pass = config.get("CONFIG_SATELLITE_PROXY_PW", '')
            sat_args = {
                'username': config["CONFIG_SATELLITE_USER"].strip(),
                'password': config["CONFIG_SATELLITE_PW"].strip(),
                'cacert': config["CONFIG_SATELLITE_CACERT"].strip(),
                'activation_key': config["CONFIG_SATELLITE_AKEY"].strip(),
                'profile_name': config["CONFIG_SATELLITE_PROFILE"].strip(),
                'proxy_host': config["CONFIG_SATELLITE_PROXY"].strip(),
                'proxy_user': sat_proxy_user.strip(),
                'proxy_pass': sat_proxy_pass.strip(),
                'flags': sat_flags
            }

    for hostname in filtered_hosts(config):
        # Subscribe to Red Hat Repositories if configured
        if rh_username:
            run_rhsm_reg(hostname, rh_username, rh_password,
                         optional=(config.get('CONFIG_RH_OPTIONAL') == 'y'),
                         proxy_server=config.get('CONFIG_RH_PROXY'),
                         proxy_port=config.get('CONFIG_RH_PROXY_PORT'),
                         proxy_user=config.get('CONFIG_RH_PROXY_USER'),
                         proxy_password=config.get('CONFIG_RH_PROXY_PASSWORD'))

        # Subscribe to RHN Satellite if configured
        if sat_url and hostname not in sat_registered:
            run_rhn_reg(hostname, sat_url, **sat_args)
            sat_registered.add(hostname)

        server = utils.ScriptRunner(hostname)
        server.append('rpm -q --whatprovides yum-utils || '
                      'yum install -y yum-utils')

        if is_rhel():
            # Installing rhos-log-collector if it is available from yum.
            server.append('yum list available rhos-log-collector && '
                          'yum -y install rhos-log-collector || '
                          'echo "no rhos-log-collector available"')

        server.execute()

        # enable RDO if it is installed locally
        manage_rdo(hostname, config)
        # enable or disable EPEL according to configuration
        manage_epel(hostname, config)

        reponame = 'rhel-server-ost-6-4-rpms'
        server.clear()
        server.append('yum install -y yum-plugin-priorities || true')
        server.append('rpm -q epel-release && yum-config-manager '
                      '--setopt="%(reponame)s.priority=1" '
                      '--save %(reponame)s' % locals())

        # Add yum repositories if configured
        CONFIG_REPO = config["CONFIG_REPO"].strip()
        if CONFIG_REPO:
            for i, repourl in enumerate(CONFIG_REPO.split(',')):
                reponame = 'packstack_%d' % i
                server.append('echo "[%(reponame)s]\nname=%(reponame)s\n'
                              'baseurl=%(repourl)s\nenabled=1\n'
                              'priority=1\ngpgcheck=0"'
                              ' > /etc/yum.repos.d/%(reponame)s.repo'
                              % locals())

        server.append("yum clean metadata")
        server.execute()
