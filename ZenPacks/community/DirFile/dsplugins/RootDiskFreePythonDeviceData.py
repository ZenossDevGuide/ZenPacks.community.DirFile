# Setup logging
import logging
log = logging.getLogger('.'.join(['zen', __name__]))

import os
import subprocess

# PythonCollector Imports
from ZenPacks.zenoss.PythonCollector.datasources.PythonDataSource import PythonDataSourcePlugin

# Twisted Imports
from twisted.internet.defer import inlineCallbacks, returnValue

class RootDiskFreePythonDeviceData(PythonDataSourcePlugin):
    """ RootDiskFree Device data source plugin """

    # List of device attributes you might need to do collection.
    proxy_attributes = (
        'zCommandUsername',
        'zKeyPath',
        )

    @classmethod
    def config_key(cls, datasource, context):

        return (
            context.id,
            datasource.getCycleTime(context),
            datasource.rrdTemplate().id,
            datasource.id,
            datasource.plugin_classname,
	    'RootDiskFreePythonDeviceData',
            )

    @inlineCallbacks
    def collect(self, config):

        log.debug('config is %s ' % (config))
        log.debug('config.datasources is %s ' % (config.datasources))
        for c in config.datasources:
            log.debug('config.datasource element is %s ' % (c))
        ds0 = config.datasources[0]
        for k,v in ds0.__dict__.items():
            log.debug('ds0 k is %s and v is %s ' % (k,v))

        # Get path to executable file, starting from this file
        #    which is in ZenPack base dir/dsplugins
        #    Executables are in ZenPack base dir / libexec
        # NOTE: If using dsplugins directory, then need to go up one to get to libexec
        thisabspath = os.path.dirname(os.path.abspath(__file__))
        libexecdir = thisabspath + '/../libexec'
        # If ds0.zKeyPath starts with ~ then it doesn't expand properly so convert to full path
        #  expanduser gives $HOME including trailing /
        homedir = os.path.expanduser("~")
        if ds0.zKeyPath.startswith('~'):
            keyPath = ds0.zKeyPath.replace('~', homedir)
        else:
            keyPath = ds0.zKeyPath
        # script is df_root_ssh.shh taking 3 parameters, zCommandUsername, keyPath, host address
        cmd = [ os.path.join(libexecdir, 'df_root_ssh.sh'), ds0.zCommandUsername, keyPath, ds0.manageIp ]
        #cmd = [ os.path.join(libexecdir, 'df_root_ssh_bad.sh'), ds0.zCommandUsername, keyPath, ds0.manageIp ]
        log.debug(' cmd is %s \n ' % (cmd) )

        value = None
        try:
            cmd_process = yield(subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE))
            # cmd_process.communicate() returns a tuple of (stdoutdata, stderrordata)
            cmd_stdout, cmd_stderr = cmd_process.communicate()
            log.debug(' stdout is %s and stderr is %s ' % (cmd_stdout, cmd_stderr))
            if not cmd_stderr:
                value = int(cmd_stdout.rstrip())
            else:    
                raise Exception('%s ' % (cmd_stderr))
        except:    
            log.exception('Error gathering RootDiskFree info - %s ' % (cmd_stderr))
            raise Exception(' %s' % (cmd_stderr))
        returnValue(value)



    def onSuccess(self, result, config):
        """
        Called only on success. After onResult, before onComplete.
        """

        log.debug( 'In success - result is %s and config is %s ' % (result, config))
        data = self.new_data()
        data['values'] = {}
        #ds0 = config.datasources[0]
        for ds in config.datasources:
            # We are forcing a single value returned from collect to populate
            # a single known datapoint called dfRootPython
            data['values'][None] = {'dfRootPython' : result}

        log.debug( 'data is %s ' % (data))
        return data

    def onError(self, result, config):
        """
        Called only on error. After onResult, before onComplete.
 
        You can omit this method if you want the error result of the collect
        method to be used without further processing. It recommended to
        implement this method to capture errors.
        """
        log.debug( 'In OnError - result is %s and config is %s ' % (result, config))
        return {
            'events': [{
                'summary': 'Error getting root df data with zenpython: %s' % result,
                'eventKey': 'RootDiskFreePythonDeviceData',
                'severity': 4,
                }],
            }


