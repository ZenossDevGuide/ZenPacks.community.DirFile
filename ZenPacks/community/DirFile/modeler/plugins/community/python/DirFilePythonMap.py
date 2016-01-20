# Module-level documentation will automatically be shown as additional
# information for the modeler plugin in the web interface.
"""
DirFilePythonMap
Python plugin using ssh scripts to gather directory and file information
"""

# When configuring modeler plugins for a device or device class, this plugin's
# name would be community.python.DirFilePythonMap because its filesystem path within
# the ZenPack is modeler/plugins/community/python/DirFilePythonMap.py. The name of the
# class within this file must match the filename.

# PythonPlugin is the base class

from Products.DataCollector.plugins.CollectorPlugin import PythonPlugin
from twisted.internet.defer import inlineCallbacks, returnValue
from twisted.internet.utils import getProcessOutputAndValue

# Classes we'll need for returning proper results from our modeler plugin's process method.
from Products.DataCollector.plugins.DataMaps import ObjectMap, RelationshipMap
from Products.ZenUtils.Utils import prepId
import collections
from itertools import chain
import re
import os

def create_dirRegex(self, device, log):
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
        return dirRegex

class DirFilePythonMap(PythonPlugin):
    # relname and modname for the PythonPlugin will be inherited by any calls to
    #    rm = self.relMap()   or om = self.objectMap()
    # No compname specified here as Dir is a component directly on the device (defaults to null string)
    # classname not required as largely deprecated. classname is the same as the module name here
    relname = 'dirs'
    modname = 'ZenPacks.community.DirFile.Dir'

    deviceProperties = PythonPlugin.deviceProperties + (
            'zCommandUsername',
            'zKeyPath',
            'zMonitorDir1',
            'zMonitorDir2',
            'zMonitorDir3',
            'zMonitorDir1File',
            'zMonitorDir2File',
            'zMonitorDir3File',
        )

    @inlineCallbacks
    def collect(self, device, log):
        """Asynchronously collect data from device. Return a deferred."""
        log.info("%s: collecting data", device.id)
        dirRegex = create_dirRegex(self, device, log)
        log.debug('dirRegex is %s' % dirRegex)

        # Modeler is under modeler/plugins/community/python
        thisabspath = os.path.dirname(os.path.abspath(__file__))
        libexecdir = thisabspath + '/../../../../libexec'
        # If device.zKeyPath starts with ~ then it doesn't expand properly so convert to full path
        #  expanduser gives $HOME including trailing /
        homedir = os.path.expanduser("~")
        if device.zKeyPath.startswith('~'):
            keyPath = device.zKeyPath.replace('~', homedir)
        else:
            keyPath = device.zKeyPath

        # scripts take 4 parameters, zCommandUsername, keyPath, host address, dirName
        dircmd = os.path.join(libexecdir, 'dudir_ssh.sh')
        filecmd = os.path.join(libexecdir, 'lsFileDiskUsed_ssh.sh')
        response = {}
        for d in dirRegex.keys():
            try:
                args = ( device.zCommandUsername, keyPath, device.manageIp, d)
                #log.debug('dircmd is %s and args is %s ' % (dircmd, args))
                dircmd_out = yield getProcessOutputAndValue(dircmd, args = args )
                # dircmd_out is a tuple of ( <stdout> , <stderr> , <exit code> )
                if dircmd_out[2] !=0: 
                    log.exception('In collect - Error gathering %s info - %s ' % (device.id, dircmd_out[1]))
                    raise Exception('In collect %s' % (dircmd_out[1]))
                    continue
                if not dircmd_out[0]:
                    log.exception('In collect - Error  gathering %s info. No result returned  ' % (device.id))
                    raise Exception('In collect - Error gathering %s info.  No result returned' % (device.id))
                    continue
                #log.debug('filecmd is %s and args is %s ' % (filecmd, args))
                filecmd_out = yield getProcessOutputAndValue(filecmd, args = args )
                if filecmd_out[2] !=0: 
                    log.exception('In collect - Error gathering %s info - %s ' % (device.id, filecmd_out[1]))
                    raise Exception('In collect %s' % (filecmd_out[1]))
                if not filecmd_out[0]:
                    log.exception('In collect - Error  gathering %s info. No result returned  ' % (device.id))
                    raise Exception('In collect - Error gathering %s info.  No result returned' % (device.id))
                # Check dircmd stdout.  Should be like:
                #    12345 /opt/zenoss/local/fredtest
                # Get the bytes used into named group bytesUsed
                # Pass the filecmd stdout as the fileOutput element to be sorted out by process
                check =  re.search(r'(?P<bytesUsed>[0-9]+)\s+/\S+$', dircmd_out[0])
                if check:
                    response[d] = {'bytesUsed': check.group('bytesUsed'), 'fileOutput': filecmd_out[0]}
                #    log.debug('response is %s ' % (response))
            except Exception, e:
                log.error(
                    "%s: %s", device.id, e)
                continue
        log.debug('Response is %s \n' % (response))
        returnValue(response)

    def process(self, device, results, log):
        log.info("Modeler %s processing data for device %s",
            self.name(), device.id)
        #log.debug('results is %s ' % (results))

        # Create dictionary where key is directory and value is file regex
        dirRegex = create_dirRegex(self, device, log)
        log.info(' dirRegex in process is %s ' % (dirRegex))

        # Setup an ordered collection of dictionaries to return data to the ApplyDataMap routine of zenmodeler
        maps = collections.OrderedDict([
            ('dirs', []),
            ('files', []),
        ])
        # Instantiate a relMap.  This inherits relname and compname from the plugin.
        rm = self.relMap()

        # result contains dictionary with:
        #  {dirname: {'bytesUsed' : < number>, 'fileOutput': < stdout string from ls -l >} , }
        #  eg.  results = {'/opt/zenoss/local/fredtest': {'fileOutput': 'total 16\n-rw-r--r-- 1 jane users  126 Jan 14 14:40 fred1.log_20151110\n-rw-r--r-- 1 jane users  434 Jan 14 14:40 fred1.log_20151116\n-rw-r--r-- 1 jane users 1047 Jan 14 14:41 fred1.log_20151202\ndrwxr-xr-x 3 jane users 4096 Dec  3 19:17 test\n', 'bytesUsed': '20290'}, '/opt/zenoss/local/fredtest/test': {'fileOutput': 'total 12\n-rw-r--r-- 1 jane users  499 Dec  2 17:38 fred2.log_20151124\n-rw-r--r-- 1 jane users  499 Dec  3 19:17 fred2.log_20151125\ndrwxr-xr-x 2 jane users 4096 Nov 29 18:17 lowertest\n', 'bytesUsed': '14587'}}
        for k, v in results.items():
                dir_id = prepId(k)
                # Add an Object Map for this directory 
                # Use prepId to ensure id is unique and doesn't include any dodgy characters like /
                # om = self.objectMap() inherits modname and compname (null) from plugin
                om = self.objectMap()
                om.id = dir_id
                om.dirName = k
                om.bytesUsed = int(v['bytesUsed'])
                for k1, v1 in om.items():
                    log.debug('dir om key is %s and value is %s' % (k1, v1))
                rm.append(om)
                # For this directory, create a map for associated files, passing this dir_id as part of compname
                fm = (self.getFileMap( device, v['fileOutput'],  dirRegex, k, 'dirs/%s' % dir_id, log))
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

        # Need this complicated setup with maps = collections.OrderedDict and the chain return
        #   to ensure that relationship maps are applied in the correct order.  Otherwise there tend
        #   to be issues trying to create relationships on objects that don't yet exist
        return list(chain.from_iterable(maps.itervalues()))

    def getFileMap(self, device, files_string, dirRegex, dir, compname, log):
        #log.debug('files_string is %s ,dirRegex is %s, dir is %s,compname is %s' % (files_string, dirRegex, dir, compname))
        file_maps = []
        for file in files_string.split('\n'):

            # component fileName attribute instance matches last field eg. fred1.log_20151110
            # 1-or-more non-whitespace char followed by 1-or-more whitspace, 1 or more times
            #    followed by 1-or-more anything  put into component variable
            #    followed by end-of-line    ie. last field
            compExp = re.search(r'(\S+\s+)+(?P<component>.+)$', file)
            if compExp:
                f = compExp.group('component')
                #log.debug('In getFileMap loop. f is %s ' % (f))
                for k, v in dirRegex.items():
                    if dir == k:                # got directory match
                        if re.search( v, f):   # check the regex
                            # Got a regex match against filename f
                            file_id = prepId(f)
                            # Don't want to inherit compname or modname from plugin as we want to set this expicitly
                            # Use ObjectMap rather than om=self.objectMap()
                            file_maps.append(ObjectMap(data = {
                                'id': file_id,
                                'fileName' : f,
                                'fileDirName' : dir,
                                'fileRegex' : v,
                                }))
                            log.info('Found dir %s and file %s match' % (dir, f))
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


