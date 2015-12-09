# Module-level documentation will automatically be shown as additional
# information for the modeler plugin in the web interface.
"""
DirFileMap
SSH plugin to gather directory and file information
"""

# When configuring modeler plugins for a device or device class, this plugin's
# name would be community.cmd.DirFileMap because its filesystem path within
# the ZenPack is modeler/plugins/community/cmd/DirFileMap.py. The name of the
# class within this file must match the filename.

# CommandPlugin is the base class that provides lots of help in modeling data
# that's available by connecting to a remote machine, running command line
# tools, and parsing their results.
from Products.DataCollector.plugins.CollectorPlugin import CommandPlugin

# Classes we'll need for returning proper results from our modeler plugin's process method.
from Products.DataCollector.plugins.DataMaps import ObjectMap, RelationshipMap
from Products.ZenUtils.Utils import prepId
import collections
from itertools import chain
import re

class DirFileMap(CommandPlugin):
    # relname and modname for the CommandPlugin will be inherited by any calls to
    #    rm = self.relMap()   or om = self.objectMap()
    # No compname specified here as Dir is a component directly on the device (defaults to null string)
    # classname not required as largely deprecated. classname is the same as the module name here
    relname = 'dirs'
    modname = 'ZenPacks.community.DirFile.Dir'

    deviceProperties = CommandPlugin.deviceProperties + (
            'zMonitorDir1',
            'zMonitorDir2',
            'zMonitorDir3',
            'zMonitorDir1File',
            'zMonitorDir2File',
            'zMonitorDir3File',
        )
    # The command to run.
    # Get directories (one per line) then a line with __SPLIT__ then files (one per line)
    # Beware this has potential to return LOTS of data
    command = (
            'find /opt/zenoss/local -type d ;'
            #'find / -type d ;'
            'echo __SPLIT__; '
            'find /opt/zenoss/local -type f'
            #'find / -type f'
            )

    def process(self, device, results, log):
        log.info("Modeler %s processing data for device %s",
            self.name(), device.id)
        #log.debug('results is %s ' % (results))

        # Create dictionary where key is directory and value is file regex
        dirRegex = {}
        if device.zMonitorDir1:
            if device.zMonitorDir1File:
                dirRegex[device.zMonitorDir1.rstrip('/')] = device.zMonitorDir1File
            else:    
                dirRegex[device.zMonitorDir1.rstrip('/')] = None
        if device.zMonitorDir2:
            if device.zMonitorDir2File:
                dirRegex[device.zMonitorDir2.rstrip('/')] = device.zMonitorDir2File
            else:    
                dirRegex[device.zMonitorDir2.rstrip('/')] = None
        if device.zMonitorDir3:
            if device.zMonitorDir3File:
                dirRegex[device.zMonitorDir3.rstrip('/')] = device.zMonitorDir3File
            else:    
                dirRegex[device.zMonitorDir3.rstrip('/')] = None

        #log.info(' dirRegex is %s ' % (dirRegex))

        # Setup an ordered collection of dictionaries to return data to the ApplyDataMap routine of zenmodeler
        maps = collections.OrderedDict([
            ('dirs', []),
            ('files', []),
        ])
        # Instantiate a relMap.  This inherits relname and compname from the plugin.
        rm = self.relMap()

        # For CommandPlugin, the results parameter to the process method will
        # be a string containing all output from the command defined above.
        # 
        # /opt/zenoss/local
        # /opt/zenoss/local/fredtest
        # __SPLIT--
        # /opt/zenoss/local/fredtest/fred2.log_20151123
        # /opt/zenoss/local/fredtest/fred2.log_20151124

        # dirlines [0] = dirs  [1] = files
        dirlines = results.split('__SPLIT__')
        for dir in dirlines[0].split('\n'):
            # Check for a dir matching a directory in our dirRegex lookup dictionary
            if dir in dirRegex.keys():
                dir_id = prepId(dir)
                # Add an Object Map for this directory 
                # Use prepId to ensure id is unique and doesn't include any dodgy characters like /
                # om = self.objectMap() inherits modname and compname (null) from plugin
                om = self.objectMap()
                om.id = dir_id
                om.dirName = dir
                for k,v in om.items():
                    log.debug('dir om key is %s and value is %s' % (k, v))
                rm.append(om)
                # For this directory, create a map for associated files, passing this dir_id as part of compname
                fm = (self.getFileMap( device, dirlines[1], dirRegex, dir, 'dirs/%s' % dir_id, log))
                log.debug('dir %s has fm  %s \n fm relname is %s and fm compname is %s ' % (om.id, fm, fm.relname, fm.compname))
                maps['files'].append(fm)
        if len(rm.maps) > 0:
            #log.info('Found matching dirs %s on %s \n dir relname is %s and dir compname is %s ' % (rm, device.id, rm.relname, rm.compname))
            pass
        else:
            log.info('No matching dirs found on %s ' % (device.id))
            return None

        # Add the rm relationships to maps['dirs']
        maps['dirs'].append(rm)
        # Next 4 lines are old code when dir_maps was created as a list rather than using rm=self.relMap()
        #maps['dirs'].append(RelationshipMap(
        #    relname = 'dirs',
        #    modname = 'ZenPacks.community.DirFile.Dir',
        #    objmaps = dir_maps))

        # Need this complicated setup with maps = collections.OrderedDict and the chain return
        #   to ensure that relationship maps are applied in the correct order.  Otherwise there tend
        #   to be issues trying to create relationships on objects that don't yet exist
        return list(chain.from_iterable(maps.itervalues()))

    def getFileMap(self, device, files_string, dirRegex, dirMatch, compname, log):
        #log.debug('files_string is %s , dirRegex is %s , compname is %s ' % (files_string, dirRegex, compname))
        file_maps = []
        for file in files_string.split('\n'):
            # Split out the filename part and the directory part
            f = file.split('/')[-1]
            d = '/'.join(file.split('/')[:-1])
            # Only consider creating a file map if the directory matches the dirMatch parameter
            if d == dirMatch:
                for k, v in dirRegex.items():
                    if d == k:                # got directory match
                        if re.search( v, f):   # check the regex
                            # Got a regex match against filename f
                            file_id = prepId(f)
                            # Don't want to inherit compname or modname from plugin as we want to set this expicitly
                            # Use ObjectMap rather than om=self.objectMap()
                            file_maps.append(ObjectMap(data = {
                                'id': file_id,
                                'fileName' : f,
                                'fileDirName' : d,
                                'fileRegex' : v,
                                }))
                            log.info('Found dir %s and file %s match' % (d, f))
                            # Get out of for k, v in dirRegex.items(): loop - don't care if matches on >1 regex
                            break

        # Return file_maps relationship map with compname passed as parameter to this method
        # Again - don't want to inherit relname, modname or compname for this relationship as we want to set them explicitly
        # Use RelationshipMap rather then rm=self.relMap()(
        return RelationshipMap(
            compname = compname,
            relname = 'files',
            modname = 'ZenPacks.community.DirFile.File',
            objmaps = file_maps)


