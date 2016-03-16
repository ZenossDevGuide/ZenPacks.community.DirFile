# Setup logging
import logging
log = logging.getLogger('.'.join(['zen', __name__]))

import os

# PythonCollector Imports
from ZenPacks.zenoss.PythonCollector.datasources.PythonDataSource import PythonDataSourcePlugin
from Products.ZenUtils.Utils import prepId
from Products.DataCollector.plugins.DataMaps import ObjectMap

# Twisted Imports
from twisted.internet.defer import inlineCallbacks, returnValue
from twisted.internet.utils import getProcessOutputAndValue

class DirDiskUsedPythonDeviceData(PythonDataSourcePlugin):
    """ DirFile Dir component data source plugin """

    # List of device attributes you might need to do collection.
    proxy_attributes = (
        'zCommandUsername',
        'zKeyPath',
        )

    @classmethod
    def config_key(cls, datasource, context):
        # context will be a Dir.  

        return (
            context.device().id,    
            datasource.getCycleTime(context),
            datasource.rrdTemplate().id,
            datasource.id,
            datasource.plugin_classname,
            context.id,
	    'DirDiskUsedPythonDeviceData',
            )

    @classmethod
    def params(cls, datasource, context):
        # context is the object that the template is applied to  - either a device or a component
        # Use params method to get at attributes or methods on the context.
        # params is run by zenhub which DOES have access to the ZODB database.
        params = {}
        params['dirName'] = ''
        if hasattr(context, 'dirName'):
            params['dirName'] = context.dirName
            params['dirId'] = context.id
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
        # script is dudir_ssh.sh taking 4 parameters, zCommandUsername, keyPath, host address, dirName
        cmd = os.path.join(libexecdir, 'dudir_ssh.sh')
        args = ( ds0.zCommandUsername, keyPath, ds0.manageIp, ds0.params['dirName'])

        # Next line should cause an error
        #args = ( ds0.zCommandUsername, keyPath, ds0.manageIp, '/blahdir')
        log.debug(' cmd is %s \n ' % (cmd) )

        try:

            cmd_stdout = yield getProcessOutputAndValue(cmd, args = args )
            log.debug( 'DirDiskUsedPythonDeviceData collect. stdout is %s and stderr is %s and exit code is %s ' % (cmd_stdout[0], cmd_stdout[1], cmd_stdout[2]))
        except Exception:
            log.exception('Error in collect gathering DirDiskUsedPythonDeviceData info - %s ' % (Exception))
            returnValue(cmd_stdout)
        returnValue(cmd_stdout)

    def onResult(self, result, config):
        """
        Called first for success and error.
 
        You can omit this method if you want the result of the collect method
        to be used without further processing.
        """
        log.debug( 'DirDiskUsedPythonDeviceData result stdout is %s and stderr is %s and exit code is %s ' % (result[0], result[1], result[2]))
        if result[2] != 0:
            log.exception('In onResult - Error in collect gathering DirDiskUsedPythonDeviceData info - %s ' % (result[1]))
            raise Exception(' %s' % (result[1]))
        if not result[0]:
            raise Exception(' %s' % ('Error in collect gathering DirDiskUsedPythonDeviceData info.  No result returned'))
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
            #result[0] in format:
            #     952   /opt/zenoss/local/fredtest
            for l in result[0].split('\n'):
                if l:
                    try:
                        # ds.component has / replaced with _ so prepId the directory name here
                        k = prepId(l.split()[1])
                        v = int(l.split()[0])
                    except:
                        raise Exception(' %s' % ('Error in collect gathering DirDiskUsedPythonDeviceData info.  Result format wrong'))
                        continue
                    log.debug('ds.component is %s' % (ds.component))
                    log.debug(' k is %s and v is %s ' % (k,v))
                    if ds.component == k:
                        data['maps'].append(
                                ObjectMap({
                                    'relname': 'dirs',
                                    'modname': 'ZenPacks.community.DirFile.Dir',
                                    'id': ds.component,
                                    'bytesUsed': v,
                                    }))
                        for datapoint_id in (x.id for x in ds.points):
                            log.debug('In datapoint loop  datapoint_id is %s ' %(datapoint_id))
                            if datapoint_id not in ['duBytes',]:
                                continue
                            dpname = '_'.join((ds.datasource, 'duBytes'))
                            log.debug('dpname is %s' % (dpname))
                            data['values'][ds.component] = {dpname : v}
                            log.debug('data[values] is %s' % (data['values']))
                            break           # got a match so get out of l loop

            # onSuccess will generate a Clear severity event to auto-close any previous error events
            data['events'].append({
                        'device': ds.device,
                        'component': ds.component,
                        'summary': 'Success getting Dudir data with zenpython',
                        'severity': 0,
                        'eventClass': '/DirFile',
                        'eventKey': ds.plugin_classname.split('.')[-1],
                        })


        # onSuccess will generate a Debug severity event - just to prove we can!
        data['events'].append({
                    'device': config.id,
                    'summary': 'Dudir',
                    'severity': 1,
                    'eventClass': '/App',
                    'eventKey': 'DirDiskUsedPythonDeviceData',
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
                'summary': 'Error getting directory du data with zenpython: %s' % result,
                'eventClass': '/DirFile',
                'eventKey': plugin,
                'severity': 4,
                'component': ds0.component,
                }],
            }

    def onComplete(self, result, config):
        """
        Called last for success and error.
 
        You can omit this method if you want the result of either the
        onSuccess or onError method to be used without further processing.
        """
        return result

