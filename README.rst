============================
ZenPacks.community.DirFile
============================


Description
===========
This ZenPack monitors particular directories and files within those directories for
existence and size.  It uses COMMAND bash scripts for both modeling and performance
data collection.

Directories and files are specified as zProperties.

This version of the ZenPack uses zenpacklib and is version 1.0.0 in the master git branch.

zenpacklib usage
----------------

This ZenPack is built with the zenpacklib library so does not have explicit code definitions for
device classes, device and component objects or zProperties.  Templates are also created through zenpacklib.
These elements are all created through the zenpack.yaml file in the main directory of the ZenPack.
See http://zenpacklib.zenoss.com/en/latest/index.html for more information on zenpacklib.

Note that if templates are changed in the zenpack.yaml file then when the ZenPack is reinstalled, the
existing templates will be renamed in the Zenoss ZODB database and the new template from the YAML file
will be installed; thus a backup is effectively taken.  Old templates should be deleted in the Zenoss GUI
when the new version is proven.


Features
========

Zenoss Device Classes
---------------------

zenpacklib creates */Server/Linux/DirFile* with:

* zPythonClass: ZenPacks.community.DirFile.DirFileDevice
* zDeviceTemplates:

  - Disk_free_df
  - Device

* zCollectorPlugins: ['zenoss.snmp.NewDeviceMap', 'zenoss.snmp.DeviceMap', 'HPDeviceMap', 'DellDeviceMap', 'zenoss.snmp.InterfaceMap', 'zenoss.snmp.RouteMap', 'zenoss.snmp.IpServiceMap', 'zenoss.snmp.HRFileSystemMap', 'zenoss.snmp.HRSWRunMap', 'zenoss.snmp.CpuMap', 'HPCPUMap', 'DellCPUMap', 'DellPCIMap', 'zenoss.snmp.SnmpV3EngineIdMap', 'community.cmd.DirFileDeviceMap', 'community.cmd.DirFileMap']
* Several templates are created accessible by this class


Device and component object classes
-----------------------------------
* DirFileDevice  - it has no new attributes

* Dir component class with attributes:

  - dirName

* File component with attributes:

  - fileName
  - fileDirName
  - fileRegex
  - monitoring_templates set to [File, FileXml] where File is shipped as part of zenpack.yaml and
    FileXml, containing custom datasource netries, is shipped in objects.xml.  

where DirFileDevice -> contains many Dir components -> contains many File components

Properties
----------

zenpacklib creates three pairs of zProperties to specify directory names to search for and a regular expression to denote
files within those directories to report on.  These are of the format:

  - zMonitorDir1
  - zMonitorDir1File


Modeler Plugins
---------------

There is no device-level modeler.

* DirFileMap which populates:

  - Directories
  - Files within the associated directory that match the regex expression


Monitoring Templates
--------------------

* Device templates
   
  - Disk_free_df with a single COMMAND datasource to run df_root.sh on remote targets to deliver disk free information, with graph

* Component templates

  - Dir with a single COMMAND datasource to gather disk usage (du) information for the directory, with graph
  - File with several COMMAND datasources (shipped in zenpack.yaml):

    - FileDiskUsed - uses du on remote target, passing filename as parameter, with graph
    - FileLsDiskUsed - uses ls on remote target and employs ZenPack parser to allocate correct data to file components, with graph
    - FileTest1WithoutCount - runs remote file_stats.sh to gather count of lines containing "without" or "test 1", 
      search string hard-coded, with graph

  - FileXml (shipped in objects.xml)    

    - without - runs remote file_stats_param.sh through a Zenapck-delivered datasource, *DirFileDataSource*, to gather 
      count of lines containing "without", where search string is supplied in template GUI, with graph
    - test_1 - runs remote file_stats_param.sh through a Zenapck-delivered datasource, *DirFileDataSource*, to gather 
      count of lines containing "test 1", where search string is supplied in template GUI, with graph


Datasources
-----------

DirFileDataSource to supply customised datasource GUI to specify a search string for file matching.  The CommandPlugin
method is used to collect the data.

Parsers
-------

The FileLsDiskUsed template uses a customised parser to allocate correct ls values to file components.


Events
------

The */DirFile* event class is shipped as part of objects.xml.


GUI modifications
-----------------


Usage
=====

The new zProperties for zMonitorDir and zMonitorDirFile should be customised for the /Server/Linux/DirFile device class and,
potentially overridden for specific devices.

Ensure that suitable values for zCommandUsername, zCommandPassword, zKeyPath and zCommandPath are customised for the device class
and potentially overridden for specific devices.

bash scripts for the command templates are shipped in the libexec directory of the ZenPack.  These should be delivered 
to the correct directory on target systems.


Requirements & Dependencies
===========================

* Zenoss Versions Supported:  4.x
* External Dependencies: 

  - The zenpacklib package that this ZenPack is built on, requires PyYAML.  This is installed as standard with Zenoss 5 and with Zenoss 4 with SP457.
    To test whether it is installed, as the zenoss user, enter the python environment and import yaml::

        python
        import yaml
        yaml

        <module 'yaml' from '/opt/zenoss/lib/python2.7/site-packages/PyYAML-3.11-py2.7-linux-x86_64.egg/yaml/__init__.py'>

    If pyYAML is not installed, install it, as the zenoss user, with::

        easy_install PyYAML

    and then rerun the test above.


* Installation Notes: 

  - Restart zenoss entirely after installation 



Download
========
Download the appropriate package for your Zenoss version from the list
below.

* Zenoss 4.0+ `Latest Package for Python 2.7`_

ZenPack installation
======================

This ZenPack can be installed from the .egg file using either the GUI or the
zenpack command line. 

To install in development mode, find the repository on github and use the *Download ZIP* button
(right-hand margin) to download a tgz file and unpack it to a local directory, say,
/code/ZenPacks .  Install from /code/ZenPacks with::
  zenpack --link --install ZenPacks.community.DirFile
  Restart zenoss after installation.

Device Support
==============

This ZenPack only requires very basic Unix commands on the traget devices.

Limitations and Troubleshooting
===============================

There is an issue sometimes with zenpacklib supporting templates with custom datasources.  
For this reason, the test_1 and without datasources and their associated graphs are shipped in
a separate FileXml template in objects.xml.  Attempts to ship them specified in zenpack.yaml
appears to result in an empty CommandTemplate field, even though ZMI shows the correct entry.
The result is that data is not collected and events are generated from zenhub complaining about
an incorrect TALES expression.

The File object class in zenpack.yaml has monitoring_templates set to [File, FileXml].


Change History
==============
* 1.0.0
   - Initial Release
* 1.0.1
   - Initial Release for PythonCollector


Screenshots
===========

See the screenshots directory.


.. External References Below. Nothing Below This Line Should Be Rendered

.. _Latest Package for Python 2.7: https://github.com/ZenossDevGuide/ZenPacks.community.DirFile/blob/master/dist/ZenPacks.community.DirFile-1.0.0-py2.7.egg?raw=true

Acknowledgements
================


