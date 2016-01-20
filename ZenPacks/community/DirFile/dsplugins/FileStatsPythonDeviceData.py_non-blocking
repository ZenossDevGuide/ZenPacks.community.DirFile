# Setup logging
import logging
log = logging.getLogger('.'.join(['zen', __name__]))

import os
import re

# PythonCollector Imports
from ZenPacks.zenoss.PythonCollector.datasources.PythonDataSource import PythonDataSourcePlugin

# Twisted Imports
from twisted.internet.defer import inlineCallbacks, returnValue
from twisted.internet.utils import getProcessOutputAndValue

class FileStatsPythonDeviceData(PythonDataSourcePlugin):
    """ DirFile File component data source plugin for test_1 and without stats"""

    # List of device attributes you might need to do collection.
    proxy_attributes = (
        'zCommandUsername',
        'zCommandPath',
        'zKeyPath',
        )

    @classmethod
    def config_key(cls, datasource, context):
        # context will be a File.  

        return (
            context.device().id,   
            datasource.getCycleTime(context),
            datasource.rrdTemplate().id,
            datasource.id,
            datasource.plugin_classname,
            context.id,
	    'FileStatsPythonDeviceData',
            )

    @classmethod
    def params(cls, datasource, context):
        # context is the object that the template is applied to  - either a device or a component
        # Use params method to get at attributes or methods on the context.
        # params is run by zenhub which DOES have access to the ZODB database.
        params = {}
        params['fileName'] = ''
        if hasattr(context, 'fileName'):
            params['fileName'] = context.fileName
        params['fileDirName'] = ''
        if hasattr(context, 'fileDirName'):
            params['fileDirName'] = context.fileDirName
        params['fileId'] = context.id
        # Need to run zenhub in debug to see log.debug statements here
        log.info(' params is %s ' % (params))
        return params

    @inlineCallbacks
    def collect(self, config):

        ds0 = config.datasources[0]
        # Get path to executable file on Zenoss collector, starting from this file
        #    which is in ZenPack base dir/datasources
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
        fileName = ds0.params['fileDirName'] + '/' + ds0.params['fileName']    
        # script is file_stats_ssh.sh taking 5 parameters, zCommandUsername, keyPath, host address, fileName, zCommandPath
        cmd = os.path.join(libexecdir, 'file_stats_ssh.sh')
        args = ( ds0.zCommandUsername, keyPath, ds0.manageIp, fileName, ds0.zCommandPath)
        # Next line should cause an error
        #args = ( ds0.zCommandUsername, keyPath, ds0.manageIp, fileName, '/blah')
        log.debug(' cmd is %s \n ' % (cmd) )

        try:
            cmd_stdout = yield getProcessOutputAndValue(cmd, args = args )
            log.debug( ' %s collect. stdout is %s and stderr is %s and exit code is %s ' % (ds0.plugin_classname, cmd_stdout[0], cmd_stdout[1], cmd_stdout[2]))
        except Exception:
            log.exception('Error in collect gathering %s info - %s ' % (ds0.plugin_classname, Exception))
            returnValue(cmd_stdout)
        returnValue(cmd_stdout)

    def onResult(self, result, config):
        """
        Called first for success and error.
 
        You can omit this method if you want the result of the collect method
        to be used without further processing.
        """
        ds0 = config.datasources[0]
        log.debug( '%s result stdout is %s and stderr is %s and exit code is %s ' % (ds0.plugin_classname, result[0], result[1], result[2]))
        if result[2] != 0:
            log.exception('In onResult - Error gathering %s info - %s ' % (ds0.plugin_classname, result[1]))
            raise Exception('In onResult %s' % (result[1]))
        if not result[0]:
            log.exception('In onResult - Error  gathering %s info. No result returned  ' % (ds0.plugin_classname))
            raise Exception('In onResult - Error gathering %s info.  No result returned' % (ds0.plugin_classname))
        return result

    def onSuccess(self, result, config):

        log.debug( 'In FileStatsPythonDeviceData success - result is %s and config is %s ' % (result, config))
        data = self.new_data()
        data['values'] = {}
        for ds in config.datasources:
            log.debug(' Start of config.datasources loop')
            # Set k to the fileId parameter passed in the params dictionary.
            #   This will be used to test against the datasource component id.
            # v is complete output returned from collect method like:
            #     File string count test ok | test_1=90 without=17
            k = ds.params['fileId']
            v = result[0]
            log.debug('ds.component is %s' % (ds.component))
            log.debug(' k is %s and v is %s ' % (k,v))
            if ds.component == k:
                # Create dictionary to hold dpname:dpvalue pairs for each file component
                #   Eg. {'statsFile_test_1': '11', 'statsFile_without': '1'}
                dpdict = {}
                for datapoint_id in (x.id for x in ds.points):
                    log.debug('In datapoint loop  datapoint_id is %s ' %(datapoint_id))
                    # Datapoint names are hard-coded here
                    if datapoint_id not in ['test_1', 'without']:
                        continue
                    dpname = '_'.join((ds.datasource, datapoint_id))
                    log.debug('dpname is %s' % (dpname))
                    # v is complete output returned from collect method like
                    #     File string count test ok | test_1=90 without=17
                    # Use regular expression re module to get values for test_1 and without
                    m = re.search(r'File string count test ok \| test_1=(?P<test_1>[0-9]*) without=(?P<without>[0-9]*)', v)
                    if m.group(datapoint_id):
                        dpdict[dpname] = m.group(datapoint_id)
                    log.debug('dpdict is %s' % (dpdict))
                data['values'][ds.component] = dpdict

        log.debug( 'data is %s ' % (data))
        return data

    def onError(self, result, config):
        """
        Called only on error. After onResult, before onComplete.
 
        You can omit this method if you want the error result of the collect
        method to be used without further processing. It recommended to
        implement this method to capture errors.
        """
        ds0 = config.datasources[0]
        plugin = ds0.plugin_classname.split('.')[-1]
        log.debug( 'In OnError - result is %s and config is %s ' % (result, config))
        return {
            'events': [{
                'summary': 'Error getting file stats data with zenpython: %s' % result,
                'eventKey': plugin,
                'severity': 4,
                }],
            }


