'''
open Abberior STED .msr files and generate bleaching curves
'''

from loci.plugins import BF

# manually import ImporterOptions, as the package name contains the "in" constant
ImporterOptions = __import__("loci.plugins.in.ImporterOptions", globals(), locals(), ['object'], -1)


from ij import ImagePlus
from ij import IJ

from glob import glob
import os

def import1ColorMSR(path):
    '''
    open MSR files as created by the 1Color2D template
    return the confocal and the STED image
    '''

    try:
        io = ImporterOptions()
        io.setId(path)
        io.setOpenAllSeries(True)
        imps = BF.openImagePlus(io)    
    except ImagePlus:
        IJ.log("ERROR while opening image file " + path)
    
    # imps[0] := confocal image, imps[1] := STED image
    return (imps[0], imps[1])


def getSumForStack(image):
    res = list()
    for i in range(1, image.getNSlices() + 1):
        image.setSlice(i)
        res.append(image.getStatistics().mean * image.getStatistics().pixelCount)
        
    return res
        


filePath = "/Users/david/Desktop/20150317_Bleaching"
fileEnding = ".msr"
# get full paths of all files in filePath ending with fileEnding
files = [os.path.join(filePath, file) for file in os.walk(filePath).next()[2] if file.endswith(fileEnding)]
# last file is single image, not stack
files = files[:-1]

outfile = open(os.path.join(filePath, "sums.csv"), "w")

results = dict()

for f in files:
    impConfocal, impSTED = import1ColorMSR(f)
    #impConfocal.show()
    results[f + "CONFOCAL"] = getSumForStack(impConfocal)
    results[f + "STED"] = getSumForStack(impSTED)
    print(getSumForStack(impSTED)[0])
    
# lexicographical order of keys -> output rows are ordered
# Note: python's sort is stable!
ranksKeys = [i[0] for i in sorted(enumerate(results.keys()), key=lambda x:x[1])]
    
outfile.write(";".join(sorted(results.keys())) + "\n")

for i in range(len(results.items()[0][1])):
    valuesAtI = list()
    for j in ranksKeys:
        valuesAtI.append(results.items()[j][1][i])
    outfile.write(";".join(map(str, valuesAtI)) + "\n")
    #print(i)
outfile.close()




