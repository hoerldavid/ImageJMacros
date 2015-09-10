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
from ij.plugin.filter import Analyzer, BackgroundSubtracter
from ij.measure import ResultsTable
from ij.gui import Roi

from ij.io import OpenDialog

from glob import glob
import os
import struct
import array
from math import *
from random import randint

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
    pixelSize = 20
    expectedFWHM = 30
    bgFactor = 3 # times FWHM -> radius for bg subtraction 
    
    measurementCh1 = 3
    measurementCh2 = 2
    
    nRandomRois = 1000
     
    expectedFWHMpx = expectedFWHM / pixelSize;

    sigma = sqrt(expectedFWHMpx)
    sigma1 = sigma
    sigma2 = sigma * sqrt(2)
    
    # channels for measurements of STED images
    imp1 = importMSR(file)[measurementCh1]
    imp2 = importMSR(file)[measurementCh2]
    # convert to float to prevent problems down the line
    imp1.setProcessor(imp1.getProcessor().convertToFloat())
    imp2.setProcessor(imp2.getProcessor().convertToFloat())
    
    # do background subtraction
    rad = expectedFWHMpx * bgFactor
    bs = BackgroundSubtracter()
    bs.rollingBallBackground(imp1.getProcessor(), rad, False, False, False, True, False)
    bs.rollingBallBackground(imp2.getProcessor(), rad, False, False, False, True, False)
    
        
    imp = imp1
    
    # select maxima -> DoG prefilter
    impDoG1 = imp.duplicate()
    impDoG2 = imp.duplicate()
    impDoG1.getProcessor().blurGaussian(sigma1)
    impDoG2.getProcessor().blurGaussian(sigma2)    
    impDoG = ImageCalculator().run("subtract create", impDoG1, impDoG2)    
    ipMax = MaximumFinder().findMaxima(impDoG.getProcessor(), 2, MaximumFinder.SINGLE_POINTS, True)
    ipMax.invertLut()
    
    
    ipMax.dilate()
    
    # calculate random rois
    
    roiCounts = []
    for i in range(nRandomRois):
        myRoi = Roi(randint(1,imp2.getWidth()-1),randint(1,imp2.getHeight()-1),3,3)
        imp2.setRoi(myRoi)
        roiCounts.append(imp2.getStatistics().mean * imp2.getStatistics().pixelCount)
        imp2.killRoi()
        
    randomRoiMeanCounts = reduce(lambda x,y: x+y, roiCounts)/nRandomRois
    
    #print(randomRoiMeanCounts)

    
    #impMax = ImagePlus("maxima", ipMax)
    #impMax.show()
    #imp1.show()
    #imp2.show()
    #return
    
    # get rm, rt and analyzer    
    rm = RoiManager.getInstance2()
    if not rm:
        rm = RoiManager()    
    rt = Analyzer.getResultsTable()
    if not rt:
        rt = ResultsTable()
        Analyzer.setResultsTable(rt)  


    rm.reset()
    
    # set PA to only accept non-touching squares (3x3 default)
    pa = ParticleAnalyzer(ParticleAnalyzer.ADD_TO_MANAGER, 0 , rt, 9, 9)
    
    impMax = ImagePlus("maxima", ipMax)
    pa.analyze(impMax)

    rois = rm.getRoisAsArray()

    means = []
    roiPixelCounts = []

    for r in rois:
        imp1.setRoi(r)
        st1 = imp1.getStatistics()
        imp2.setRoi(r)
        st2 = imp2.getStatistics()
        # print st.mean / st.stdDev
        means.append((st1.mean, st2.mean))
        roiPixelCounts.append(st1.pixelCount)
        
        imp1.killRoi()
        imp2.killRoi()

    for m in means:
        print(m[1]/randomRoiMeanCounts)

    return
    st = imp.getStatistics()
    totalMean = st.mean
    totalPixel = st.pixelCount

    rows = [[means[i], roiPixelCounts[i], totalMean, totalPixel] for i in range(len(means))]

    return rows
    

def main():
    
    od = OpenDialog("Select File to analyze")
    if not od.getPath():
        return
    
    spotAnalysisSingle(od.getPath())
    
    

    return
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