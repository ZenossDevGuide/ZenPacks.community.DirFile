import Products.ZenModel.BasicDataSource as BasicDataSource
from Products.ZenModel.ZenPackPersistence import ZenPackPersistence

from zope.component import adapts
from zope.interface import implements

from Products.Zuul.form import schema
from Products.Zuul.infos import ProxyProperty
from Products.Zuul.infos.template import CommandDataSourceInfo
from Products.Zuul.interfaces.template import ICommandDataSourceInfo
from Products.Zuul.utils import ZuulMessageFactory as _t
from DateTime import DateTime
from Products.PageTemplates.Expressions import getEngine
from Products.ZenUtils.ZenTales import talesCompile

# Setup logging so it includes the ZenPack name
import logging
log = logging.getLogger('.'.join(['zen', __name__]))

class DirFileDataSource(ZenPackPersistence, BasicDataSource.BasicDataSource):
    """ Get  DirFile data using Command """

    ZENPACKID = 'ZenPacks.community.DirFile'

    # Friendly name for your data source type in the drop-down selection.
    sourcetypes = ('DirFileDataSource',)
    sourcetype = sourcetypes[0]

    # Standard fields in the datasource - with overriden values
    #    (which can be overriden again in the template )
    component = '${here/id}'
    # Note: Event Class must be defined to see this default in GUI
    eventClass = '/DirFile'
    cycletime = 600
    parser = "Auto"
    usessh = True    
    commandTemplate = 'file_stats_param.sh ${here/fileDirName}/${here/fileName}'

    stringToFind = ''
    _properties = BasicDataSource.BasicDataSource._properties + (
        {'id': 'stringToFind', 'type': 'string', 'mode': 'w'},
    )
    _relations = BasicDataSource.BasicDataSource._relations + (
        )

    def getDescription(self):
        # getDescription in BasicDataSource only sets values if type = COMMAND or SNMP
        # This is the comment under Source that you see in the template against the datasource
        if self.usessh:
            return self.commandTemplate + " " + self.stringToFind + " over SSH"
        else:
            return self.commandTemplate + " " + self.stringToFind

    def useZenCommand(self):
        # useZenCommand in BasicDataSource only returns True for sourcetype == 'COMMAND'
        return True

    def getCommand(self, context, cmd=None):
        # No getCommand in BasicDataSource  - inherits from 
        #   SimpleRRDDataSource inherits from RRDDataSource
        # Duplicate getCommand from RRDDataSource and add  stringToFind
        # Perform a TALES eval on the expression using self
        if cmd is None:
            cmd = self.commandTemplate
        log.debug(' Raw cmd is %s ' % (cmd))
        if self.stringToFind:
            #Need to ensure any white space is wrapped in quotes
            cmd = cmd + ' "' + self.stringToFind + '"'
        log.debug(' cmd with stringToFind is %s ' % (cmd))
        if not cmd.startswith('string:') and not cmd.startswith('python:'):
            cmd = 'string:%s' % cmd
        log.debug(' cmd after string check is %s ' % (cmd))
        compiled = talesCompile(cmd)
        d = context.device()
        environ = {'dev' : d,
                   'device': d,
                   'devname': d.id,
                   'ds': self,
                   'datasource': self,
                   'here' : context,
                   'zCommandPath' : context.zCommandPath,
                   'nothing' : None,
                   'now' : DateTime() }
        log.debug(' environ  is %s ' % (environ))
        res = compiled(getEngine().getContext(environ))
        log.debug(' res compiled engine is %s ' % (res))
        if isinstance(res, Exception):
            raise res
        res = self.checkCommandPrefix(context, res)
        log.debug(' res to return is %s ' % (res))
        return res

    def addDataPoints(self):
        # Add a datapoint called matches if it isn't defined in the template
        if not hasattr(self.datapoints, 'matches'):
            # there is no manage_addBasicDataPoint method - only manage_addRRDDataPoint
            self.manage_addRRDDataPoint('matches')


class IDirFileDataSourceInfo(ICommandDataSourceInfo):
    """Interface that creates the web form for this data source type.
       These entries define fields you see in the GUI
       The group statement is to keep attributes together on the GUI.
    """

    stringToFind = schema.TextLine(
        title = _t(u'Search String'),
        group = _t('stringToFind'))

class DirFileDataSourceInfo(CommandDataSourceInfo):
    """ Adapter between IDirFileSourceInfo and DirFileSource 
        These entries define the default data that you see in GUI fields
    """

    implements(IDirFileDataSourceInfo)
    adapts(DirFileDataSource)

    stringToFind = ProxyProperty('stringToFind')

    # Component template doesn't run over SSH in GUI anyway, so disable 
    testable = False

