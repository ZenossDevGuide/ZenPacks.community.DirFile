from ZenPacks.zenoss.PythonCollector.datasources.PythonDataSource import PythonDataSource, PythonDataSourcePlugin

from zope.component import adapts
from zope.interface import implements
from Products.Zuul.form import schema
from Products.Zuul.infos import ProxyProperty
from Products.Zuul.infos.template import RRDDataSourceInfo
from Products.Zuul.interfaces import IRRDDataSourceInfo
from Products.Zuul.utils import ZuulMessageFactory as _t

# Twisted Imports
from twisted.internet.defer import inlineCallbacks, returnValue
from twisted.internet.utils import getProcessOutputAndValue

import os
import re

# Setup logging so it includes the ZenPack name
import logging
log = logging.getLogger('.'.join(['zen', __name__]))

class DirFilePythonDataSource(PythonDataSource):
    """ Get  DirFile data using Command """

    ZENPACKID = 'ZenPacks.community.DirFile'

    # Friendly name for your data source type in the drop-down selection.
    sourcetypes = ('DirFilePythonDataSource',)
    sourcetype = sourcetypes[0]

    # Standard fields in the datasource - with overriden values
    #    (which can be overriden again in the template )
    component = '${here/id}'
    # Note: Event Class must be defined to see this default in GUI
    eventClass = '/DirFile'
    # NB cycletime is string rather than  int in PythonDataSource
    cycletime = '600'

    stringToFind = ''
    _properties = PythonDataSource._properties + (
        {'id': 'stringToFind', 'type': 'string', 'mode': 'w'},
    )

    # Collection plugin for this type. Defined below in this file.
    plugin_classname = ZENPACKID + '.datasources.DirFilePythonDataSource.DirFilePythonDataSourcePlugin'

    def addDataPoints(self):
        # Add a datapoint called matches if it isn't defined in the template
        if not hasattr(self.datapoints, 'matches'):
            # there is no manage_addBasicDataPoint method - only manage_addRRDDataPoint
            self.manage_addRRDDataPoint('matches')


class IDirFilePythonDataSourceInfo(IRRDDataSourceInfo):
    """Interface that creates the web form for this data source type.
       These entries define fields you see in the GUI
       The group statement is to keep attributes together on the GUI.
    """
    stringToFind = schema.TextLine(
        title = _t(u'Search String'),
        group = _t('stringToFind'))

class DirFilePythonDataSourceInfo(RRDDataSourceInfo):
    """ Adapter between IDirFileSourceInfo and DirFileSource 
        These entries define the default data that you see in GUI fields
    """
    implements(IDirFilePythonDataSourceInfo)
    adapts(DirFilePythonDataSource)

    stringToFind = ProxyProperty('stringToFind')

class DirFilePythonDataSourcePlugin(PythonDataSourcePlugin):
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
            'FileStatsPythonDeviceDataDataSource',
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
        params['stringToFind'] = datasource.talesEval(datasource.stringToFind, context)
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
        # script is file_stats_ssh.sh taking 6 parameters, zCommandUsername, keyPath, 
        #         host address, fileName, zCommandPath, searchstring
        cmd = os.path.join(libexecdir, 'file_stats_param_ssh.sh')
        args = ( ds0.zCommandUsername, keyPath, ds0.manageIp, fileName, ds0.zCommandPath, ds0.params['stringToFind'])
        # Next line should cause an error
        #args = ( ds0.zCommandUsername, keyPath, ds0.manageIp, fileName, '/blah', ds0.params['stringToFind'])
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

        log.debug( 'In FileStatsPythonDeviceDataDataSource success - result is %s and config is %s ' % (result, config))
        data = self.new_data()
        data['values'] = {}
        for ds in config.datasources:
            log.debug(' Start of config.datasources loop')
            # Set k to the fileId parameter passed in the params dictionary.
            #   This will be used to test against the datasource component id.
            # v is complete output returned from collect method like:
            #     File string count test ok | matches=30
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
                    if datapoint_id not in ['matches']:
                        continue
                    dpname = '_'.join((ds.datasource, datapoint_id))
                    log.debug('dpname is %s' % (dpname))
                    # v is complete output returned from collect method like
                    #     File string count test ok | test_1=90 without=17
                    # Use regular expression re module to get values for test_1 and without
                    m = re.search(r'File string count test ok \| matches=(?P<matches>[0-9]*)', v)
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
                'summary': 'Error getting file stats data with zenpython DirFilePythonDataSource: %s' % result,
                'eventClass': '/DirFile',
                'eventKey': plugin,
                'severity': 4,
                }],
            }


