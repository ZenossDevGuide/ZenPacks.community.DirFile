from . import zenpacklib

zenpacklib.load_yaml()

import sys
from Products.ZenUtils.Utils import monkeypatch
from Products.ZenUtils.ZenTales import talesEvalStr

# SshClient does a relative import of CollectorClient from
#    /opt/zenoss/Products/DataCollector/CollectorClient.py. 
# The standard CollectorClient class has an __init__ like:
#    def __init__(self, hostname, ip, port, plugins=None, options=None,
#                    device=None, datacollector=None, alog=None):        
# Note first 3 parameters are mandatory ( args[0] to args[2] ), plugins
#  is first optional at args[3]. device may be args[5]
#
# Normally one cannot pass TALES expressions to a command.  This code
# does a monkeypatch to the relative CollectorClient module already in
# sys.modules to check for ${ syntax and performs a TALES evaluation.

if 'CollectorClient' in sys.modules:
    CollectorClient = sys.modules['CollectorClient']

    @monkeypatch(CollectorClient.CollectorClient)
    def __init__(self, *args, **kwargs):
        # original is injected into locals by the monkeypatch decorator.
        original(self, *args, **kwargs)

        # Reset cmdmap and _commands.
        self.cmdmap = {}
        self._commands = []

        # Get plugins from args or kwargs.
        plugins = kwargs.get('plugins')
        if plugins is None:
            if len(args) > 3:
                plugins = args[3]
            else:
                plugins = []

        # Get device from args or kwargs.
        device = kwargs.get('device')
        if device is None:
            if len(args) > 5:
                device = args[5]
            else:
                device = None

        # Do TALES evaluation of each plugin's command.
        for plugin in plugins:
            if '${' in plugin.command:
                try:
                    command = talesEvalStr(plugin.command, device)
                except Exception:
                    CollectorClient.log.exception(
                        "%s - command parsing error",
                        device.id)

                    continue
            else:
                command = plugin.command

            self.cmdmap[command] = plugin
            self._commands.append(command)

