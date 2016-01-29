# Setup logging
import logging
log = logging.getLogger('.'.join(['zen', __name__]))

import os
import subprocess

# PythonCollector Imports
from ZenPacks.zenoss.PythonCollector.datasources.PythonDataSource import PythonDataSourcePlugin

# Twisted Imports
from twisted.internet.defer import inlineCallbacks, returnValue
from twisted.internet.utils import getProcessOutputAndValue

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
        # script is df_root_ssh.sh taking 3 parameters, zCommandUsername, keyPath, host address
        cmd = os.path.join(libexecdir, 'df_root_ssh.sh')
        #cmd = os.path.join(libexecdir, 'df_root_ssh_bad.sh')
        args = ( ds0.zCommandUsername, keyPath, ds0.manageIp)
        log.debug(' cmd is %s \n ' % (cmd) )

        try:
            cmd_stdout = yield getProcessOutputAndValue(cmd, args = args )
            log.debug( 'RootDiskFree collect. stdout is %s and stderr is %s and exit code is %s ' % (cmd_stdout[0], cmd_stdout[1], cmd_stdout[2]))
        except Exception:    
            log.exception('Error in collect gathering RootDiskFree info - %s ' % (Exception))
        returnValue(cmd_stdout)

    def onResult(self, result, config):
        """
        Called first for success and error.
 
        You can omit this method if you want the result of the collect method
        to be used without further processing.
        """
        log.debug( 'RootDiskFree result. stdout is %s and stderr is %s and exit code is %s ' % (result[0], result[1], result[2]))
        # Check that the command exit code is 0 and that there is a non-null result for stdout
        if result[2] != 0:
            log.exception('In onResult - Error in collect gathering RootDiskFree info - %s ' % (result[1]))
            raise Exception(' %s' % (result[1]))
        if not result[0]:
            raise Exception(' %s' % ('Error in collect gathering RootDiskFree info.  No result returned'))
        return result



    def onSuccess(self, result, config):
        """
        Called only on success. After onResult, before onComplete.
        """

        # CAN log result here as Deferred is now instantiated
        log.debug( 'In RootDiskFree success - result is %s and config is %s ' % (result, config))
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
                'eventClass': '/DirFile',
                'eventKey': 'RootDiskFreePythonDeviceData',
                'severity': 4,
                }],
            }


