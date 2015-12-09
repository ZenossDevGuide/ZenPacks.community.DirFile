##############################################################################
# Parser for a File component
#############################################################################
from Products.ZenRRD.ComponentCommandParser import ComponentCommandParser
import logging
log = logging.getLogger('.'.join(['zen', __name__]))
log.info('Start of File parser by JC')

# The parser class name MUST match the object class name ie. File
class File(ComponentCommandParser):

    # output from ls -l
    #total 16
    #-rw-r--r-- 1 jane users  119 Dec  2 17:36 fred1.log_20151110
    #-rw-r--r-- 1 jane users  559 Dec  2 17:37 fred1.log_20151116
    #-rw-r--r-- 1 jane users  500 Dec  3 11:09 fred1.log_20151202
    #drwxr-xr-x 3 jane users 4096 Dec  2 17:38 test

    # Split components on newline
    componentSplit = '\n'

    # component fileName attribute instance matches last field eg. fred1.log_20151110
    # 1-or-more non-whitespace char followed by 1-or-more whitspace, 1 or more times
    #    followed by 1-or-more anything  put into component variable
    #    followed by end-of-line    ie. last field
    componentScanner = r'(\S+\s+)+(?P<component>.+)$'

    # Get 5th field that must be digits
    # 1-or-more non-whitespace char followed by 1-or-more whitspace, 4 times
    #    followed by 1-or-more digits  put into lsBytesUsed variable
    # lsBytesUsed MUST match datapoint name in template
    scanners = [
        r'(\S+\s+){4}(?P<lsBytesUsed>[0-9]+)'    
        ]
    
    # Component object attribute that componentScanner instance value must match
    componentScanValue = 'fileName'
