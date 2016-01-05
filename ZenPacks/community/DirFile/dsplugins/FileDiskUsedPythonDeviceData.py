# Setup logging
import logging
log = logging.getLogger('.'.join(['zen', __name__]))

import os
import subprocess

# PythonCollector Imports
from ZenPacks.zenoss.PythonCollector.datasources.PythonDataSource import PythonDataSourcePlugin

# Twisted Imports
from twisted.internet.defer import inlineCallbacks, returnValue

class FileDiskUsedPythonDeviceData(PythonDataSourcePlugin):
    """ DirFile File component data source plugin """

    # List of device attributes you might need to do collection.
    proxy_attributes = (
        'zCommandUsername',
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
	    'FileDiskUsedPythonDeviceData',
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
        # script is dufile_ssh.sh taking 4 parameters, zCommandUsername, keyPath, hostname, fileName
        cmd = [ os.path.join(libexecdir, 'dufile_ssh.sh'), ds0.zCommandUsername, keyPath, ds0.device, fileName ]
        # Next line should cause an error
        #cmd = [ os.path.join(libexecdir, 'dufile_ssh.sh'), ds0.zCommandUsername, keyPath, ds0.device, '/blah' ]
        log.debug(' cmd is %s \n ' % (cmd) )

        retDict = {}
        try:
            cmd_process = yield(subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE))
            # cmd_process.communicate() returns a tuple of (stdoutdata, stderrordata)
            cmd_stdout, cmd_stderr = cmd_process.communicate()
            log.info(' stdout is %s and stderr is %s ' % (cmd_stdout, cmd_stderr))
            if not cmd_stderr:
                # The ultimate result from the plugin is a dictionary where keys are component ids so
                #   return a dictionary here with the fileId (not name) as key
                retDict = {ds0.params['fileId'] : int(cmd_stdout.rstrip())}
                log.debug('ds0.params is %s and retDict = %s ' % (ds0.params, retDict))
            else:    
                raise Exception('%s ' % (cmd_stderr))
        except:    
            log.exception('Error gathering FileDiskUsed info - %s ' % (cmd_stderr))
            raise Exception(' %s' % (cmd_stderr))
        returnValue(retDict)

    def onResult(self, result, config):
        """
        Called first for success and error.
 
        You can omit this method if you want the result of the collect method
        to be used without further processing.
        """
        log.debug( 'result is %s ' % (result))
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

        log.debug( 'In success - result is %s and config is %s ' % (result, config))
        data = self.new_data()
        data['values'] = {}
        for ds in config.datasources:
            log.debug(' Start of config.datasources loop')
            for k, v in result.items():
                log.debug('ds.component is %s' % (ds.component))
                log.debug(' k is %s and v is %s ' % (k,v))
                if ds.component == k:
                    for datapoint_id in (x.id for x in ds.points):
                        log.debug('In datapoint loop  datapoint_id is %s ' %(datapoint_id))
                        if datapoint_id not in ['duBytes',]:
                            continue
                        dpname = '_'.join((ds.datasource, 'duBytes'))
                        log.debug('dpname is %s' % (dpname))
                        log.debug('data[values] is %s' % (data['values']))
                        data['values'][ds.component] = {dpname : v}

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
                'summary': 'Error getting file du data with zenpython: %s' % result,
                'eventKey': 'FileDiskUsedPythonDeviceData',
                'severity': 4,
                }],
            }

