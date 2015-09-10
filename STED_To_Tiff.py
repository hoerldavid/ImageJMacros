'''
open Abberior STED .msr files and generate bleaching curves
'''

from loci.plugins import BF


# manually import ImporterOptions, as the package name contains the "in" constant
ImporterOptions = __import__("loci.plugins.in.ImporterOptions", globals(), locals(), ['object'], -1)


from ij import ImagePlus
from ij import IJ

from java.lang import Integer, Short

from glob import glob
import os
import struct
import array

def importMSR(path):
    '''
    open MSR files
    returns array of stacks
    '''

    try:
        io = ImporterOptions()
        io.setId(path)
        io.setOpenAllSeries(True)
        imps = BF.openImagePlus(io)    
    except ImagePlus:
        IJ.log("ERROR while opening image file " + path)
    
    # imps[0] := confocal image, imps[1] := STED image
    return (imps)

def main():
    '''
    main 
    '''
    filePath = "/Volumes/vg0.lv0.voxdata2/STED/dh/20150825_edu_pcna_darmstadt/"
    fileEnding = ".msr"
    # get full paths of all files in filePath ending with fileEnding
    files = [os.path.join(filePath, file) for file in os.walk(filePath).next()[2] if file.endswith(fileEnding)]
   
    
    for f in files:
        imps = importMSR(f)
        #impConfocal.show()
        if len(imps) == 3:
        	IJ.saveAsTiff(imps[1], os.path.join(f.rsplit(os.path.sep, 1)[0], "export", f.rsplit(os.path.sep, 1)[1]))
        if len(imps) == 5:
        	IJ.saveAsTiff(imps[2], os.path.join(f.rsplit(os.path.sep, 1)[0], "export", f.rsplit(os.path.sep, 1)[1]))
        if len(imps) == 7:
            print(f)
if __name__ == "__main__":
    main()