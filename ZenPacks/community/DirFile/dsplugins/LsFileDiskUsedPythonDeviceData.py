# Setup logging
import logging
log = logging.getLogger('.'.join(['zen', __name__]))

import os
import re

# PythonCollector Imports
from twisted.internet.utils import getProcessOutputAndValue

# Twisted Imports
from twisted.internet.defer import inlineCallbacks, returnValue
from ZenPacks.zenoss.PythonCollector.datasources.PythonDataSource import PythonDataSourcePlugin

class LsFileDiskUsedPythonDeviceData(PythonDataSourcePlugin):
    """ DirFile File component data source plugin """

    # List of device attributes you might need to do collection.
    proxy_attributes = (
        'zCommandUsername',
        'zKeyPath',
        )

    @classmethod
    def config_key(cls, datasource, context):
        # context will be a File.  
        # One command to a device supplies data for all context.id's 
        #   so context.id not needed in config_key

        return (
            context.device().id,   
            datasource.getCycleTime(context),
            datasource.rrdTemplate().id,
            datasource.id,
            datasource.plugin_classname,
            context.fileDirName,
	    'LsFileDiskUsedPythonDeviceData',
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
        log.info(' LsFileDiskUsedPythonDeviceData params is %s ' % (params))
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
        # script is lsFileDiskUsed_ssh.sh taking 4 parameters, zCommandUsername, keyPath, host address, fileDirName
        cmd = os.path.join(libexecdir, 'lsFileDiskUsed_ssh.sh')
        args = ( ds0.zCommandUsername, keyPath, ds0.manageIp, ds0.params['fileDirName'])
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
        """
        Called only on success. After onResult, before onComplete.
 
        You should return a data structure with zero or more events, values
        and maps.
        Note that values is a dictionary and events and maps are lists.

        return {
            'events': [{
                'summary': 'successful collection',
                'eventKey': 'myPlugin_result',
                'severity': 0,
                },{
                'summary': 'first event summary',
                'eventKey': 'myPlugin_result',
                'severity': 2,
                },{
                'summary': 'second event summary',
                'eventKey': 'myPlugin_result',
                'severity': 3,
                }],
 
            'values': {
                None: {  # datapoints for the device (no component)
                    'datapoint1': 123.4,
                    'datapoint2': 5.678,
                    },
                'cpu1': {
                    'user': 12.1,
                    nsystem': 1.21,
                    'io': 23,
                    }
                },
 
            'maps': [
                ObjectMap(...),
                RelationshipMap(..),
                ]
            }
            """

        log.debug( 'In LsFileDiskUsedPythonDeviceData success - result is %s and config is %s ' % (result, config))
        data = self.new_data()
        data['values'] = {}

        # The ultimate result from the plugin is a dictionary where keys are component ids so
        #   return a dictionary here with the fileId (not name) as key
        # result[0] is the complete string returned from the command, like: 
        #
        #total 16
        #-rw-r--r-- 1 jane users  119 Dec  2 17:36 fred1.log_20151110
        #-rw-r--r-- 1 jane users  559 Dec  2 17:37 fred1.log_20151116
        #-rw-r--r-- 1 jane users  500 Dec  3 11:09 fred1.log_20151202
        #drwxr-xr-x 3 jane users 4096 Dec  2 17:38 test
        #
        #Use regular expression re module to allocate file sizes to file names
        # component fileName attribute instance matches last field eg. fred1.log_20151110
        # 1-or-more non-whitespace char followed by 1-or-more whitspace, 1 or more times
        #    followed by 1-or-more anything  put into component variable
        #    followed by end-of-line    ie. last field
        componentScanner = r'(\S+\s+)+(?P<component>.+)$'
        # Get 5th field that must be digits
        # 1-or-more non-whitespace char followed by 1-or-more whitspace, 4 times
        #    followed by 1-or-more digits  put into lsBytesUsed variable
        scanners = r'(\S+\s+){4}(?P<lsBytesUsed>[0-9]+)'

        for ds in config.datasources:
            log.debug(' Start of config.datasources loop')
            for l in result[0].split('\n'):
                if l:
                    try:
                        k = re.search(componentScanner, l)
                        v = re.search(scanners,l)
                    except:
                        raise Exception('In onSuccess - Error gathering %s info.  Result format wrong') % (ds.plugin_classname,)
                    if k and v:
                        k = k.group('component')
                        v = v.group('lsBytesUsed')
                        log.debug('ds.component is %s' % (ds.component))
                        log.debug(' k is %s and v is %s ' % (k,v))
                        if ds.component == k:
                            # For each file component, build the dpdict with {dpname: <datapoint value> }
                            # Currently only one hard-coded datapoint called lsBytesUsed
                            dpdict = {}
                            for datapoint_id in (x.id for x in ds.points):
                                log.debug('In datapoint loop  datapoint_id is %s ' %(datapoint_id))
                                if datapoint_id not in ['lsBytesUsed',]:
                                    continue
                                dpname = '_'.join((ds.datasource, 'lsBytesUsed'))
                                dpdict[dpname] = v
                                log.debug('dpname is %s' % (dpname))
                                log.debug('dpdict is %s' % (dpdict))
                            data['values'][ds.component] = dpdict
                            break               # got a match so get out of l loop

            # onSuccess will generate a Clear severity event to auto-close any previous error events
            data['events'].append({
                        'device': ds.device,
                        'component': ds.component,
                        'summary': 'Success getting file ls data with zenpython',
                        'severity': 0,
                        'eventClass': '/DirFile',
                        'eventKey': ds.plugin_classname.split('.')[-1],
                        })


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
        log.debug( 'In onError - result is %s and config is %s ' % (result, config))
        return {
            'events': [{
                'summary': 'Error getting file ls data with zenpython: %s' % result,
                'eventClass': '/DirFile',
                'eventKey': plugin,
                'severity': 4,
                'component': ds0.component,
                }],
            }


