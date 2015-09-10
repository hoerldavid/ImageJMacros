'''
Analyze AB lawn STED images

detect single spots by DoG + find Maxima
cut 3x3 pixels around and integrate density

'''

from loci.plugins import BF


# manually import ImporterOptions, as the package name contains the "in" constant
ImporterOptions = __import__("loci.plugins.in.ImporterOptions", globals(), locals(), ['object'], -1)


from ij import ImagePlus
from ij import IJ
from ij.plugin import ImageCalculator

from ij.plugin.filter import MaximumFinder, ParticleAnalyzer

from java.lang import Integer, Short

from ij.plugin.frame import RoiManager
from ij.plugin.filter import Analyzer
from ij.measure import ResultsTable

from glob import glob
import os
import struct
import array
from math import *

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
    
    return (imps)

def spotAnalysisSingle(file):
    
    # constants - change if necessary
    pixelSize = 10
    expectedFWHM = 30
     
    expectedFWHMpx = expectedFWHM / pixelSize;

    sigma = expectedFWHMpx / (2*sqrt(2*log(2)))
    sigma1 = sigma / sqrt(2)
    sigma2 = sigma * sqrt(2)
    
    # second measurement = STED image
    imp = importMSR(file)[1]
    
    imp.setProcessor(imp.getProcessor().convertToFloat())
    
    impDoG1 = imp.duplicate()
    impDoG2 = imp.duplicate()

    impDoG1.getProcessor().blurGaussian(sigma1)
    impDoG2.getProcessor().blurGaussian(sigma2)
    
    impDoG = ImageCalculator().run("subtract create", impDoG1, impDoG2)
    
    ipMax = MaximumFinder().findMaxima(impDoG.getProcessor(), 2, MaximumFinder.SINGLE_POINTS, True)
    ipMax.invertLut()
    ipMax.dilate()
    
    # get rm, rt and analyzer    
    rm = RoiManager.getInstance2()
    if not rm:
        rm = RoiManager()    
    rt = Analyzer.getResultsTable()
    if not rt:
        rt = ResultsTable()
        Analyzer.setResultsTable(rt)  


    rm.reset()
    pa = ParticleAnalyzer(ParticleAnalyzer.ADD_TO_MANAGER, 0 , rt, 9, 9)

    
    impMax = ImagePlus("maxima", ipMax)
    pa.analyze(impMax)

    rois = rm.getRoisAsArray()

    means = []
    roiPixelCounts = []

    for r in rois:
        imp.setRoi(r)
        st = imp.getStatistics()
        # print st.mean / st.stdDev
        means.append(st.mean)
        roiPixelCounts.append(st.pixelCount)
        imp.killRoi()
	
    st = imp.getStatistics()
    totalMean = st.mean
    totalPixel = st.pixelCount

    rows = [[means[i], roiPixelCounts[i], totalMean, totalPixel] for i in range(len(means))]

    return rows
    

def main():
    
    inputDir = "/Users/david/Desktop/20150828_abslides/"

    outFile = os.path.join(inputDir, "results.csv")
    outFD = open(outFile, "w")

    outFD.write("\t".join(["cond", "idx", "spotMean", "spotPx", "totalMean", "totalPx"]) + "\n")
    
    files = [os.path.join(inputDir, f) for f in os.walk(inputDir).next()[2] if f.endswith(".msr")]
    for f in files:
        cond =  f.split(os.path.sep)[-1].rstrip(".msr").rsplit("_", 1)[0]
        idx = f.split(os.path.sep)[-1].rstrip(".msr").rsplit("_", 1)[1]
        rows = spotAnalysisSingle(f)

        outrows = [[cond, idx] + rows[i] for i in range(len(rows))]

        for r in outrows:
        	outFD.write("\t".join(map(str, r)) + "\n")

        print "processed " + f

    outFD.close()
    print "DONE"
    
    
    
    
if __name__ == "__main__":
    main()
    
    