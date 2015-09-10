import sys, os
import re
from inspect import getsourcefile

from ij.plugin import Resizer
from ij.io import DirectoryChooser, OpenDialog
from ij import IJ, ImagePlus
from ij.process import StackConverter, StackProcessor

# import a module in ImageJ
def dummy():
    pass
sys.path.append(getsourcefile(dummy).rsplit(os.path.sep, 1)[0] + os.path.sep + "ijplugin-util")
import ImspectorIO


def main():
    dc = DirectoryChooser("pick directory!")
    inputDir = os.walk(dc.getDirectory()).next()
    
    files = [os.path.join(inputDir[0],f) for f in inputDir[2]]
    print files
    
    outFd = open(os.path.join(inputDir[0], "res.csv"), "w")
    outFd.write(";".join(["laser", "dwell", "rep", "channel", "signal"]) + "\n")
    
    p = re.compile("(.+?)_(.+?)_([0-9]+?)\.msr")
    for f in files:
        m = p.match(f.split(os.path.sep)[-1])
        if m:
            print m.groups()
            
            imps = ImspectorIO.openMSR(f)
            
            p1 = ImspectorIO.impToFloatPixels(imps[0])
            p2 = ImspectorIO.impToFloatPixels(imps[1])
            
            ImspectorIO.writePixelsToCSV(outFd, p1, list(m.groups()) + ["1"])
            ImspectorIO.writePixelsToCSV(outFd, p2, list(m.groups()) + ["2"])
            
            
    outFd.close()


if __name__ == "__main__":
    main()