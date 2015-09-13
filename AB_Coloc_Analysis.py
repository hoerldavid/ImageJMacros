'''
Analyze AB lawn STED images

detect single spots by DoG + find Maxima
cut 3x3 pixels around and integrate density / compare to mean / quantiles

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

def getQuantile(l, p):
    '''
    get p-quantile of elements in list (sorted ascending)
    '''
    idx = float(p)*(len(l)-1)
    
    if ceil(idx) == idx:
        return(sorted(l)[int(idx)])
    else:
        return((sorted(l)[int(floor(idx))] + sorted(l)[int(ceil(idx))]) / 2)
        
    

def spotAnalysisSingle(file):
    
    # constants - change if necessary
    pixelSize = 20
    expectedFWHM = 30
    bgFactor = 3 # times FWHM -> radius for bg subtraction 
    
    measurementCh1 = 2
    measurementCh2 = 3
    
    nRandomRois = 1000
    
    randomRoiQuantile = 0.95
     
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
    bs.rollingBallBackground(imp1.getProcessor(), rad, False, False, False, False, False)
    bs.rollingBallBackground(imp2.getProcessor(), rad, False, False, False, False, False)
    
        
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
    
    ipRandrois = imp1.getProcessor().createProcessor(imp1.getWidth(), imp1.getHeight())
    
    roiCounts = []
    for i in range(nRandomRois):
        myRoi = Roi(randint(1,imp2.getWidth()-1),randint(1,imp2.getHeight()-1),3,3)
        imp2.setRoi(myRoi)
        roiCounts.append(imp2.getStatistics().mean * imp2.getStatistics().pixelCount)
        imp2.killRoi()
        myRoi.drawPixels(ipRandrois)
        
    #for r in roiCounts:
    #    print(r)

    #return
    
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
    
    ipNoColoc = imp1.getProcessor().createProcessor(imp1.getWidth(), imp1.getHeight())
    ipColoc = imp1.getProcessor().createProcessor(imp1.getWidth(), imp1.getHeight())

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
        
        if means[-1][1] * roiPixelCounts[-1] / getQuantile(roiCounts, randomRoiQuantile) > 1:
            r.drawPixels(ipColoc)
        else:
            r.drawPixels(ipNoColoc)

    for i in range(len(means)):
        print(means[i][1] * roiPixelCounts[i] / getQuantile(roiCounts, randomRoiQuantile))


    imp1.setTitle("ch1")
    imp2.setTitle("ch2")
    
    impRandrois = ImagePlus("random rois", ipRandrois)
    impColoc = ImagePlus("coloc", ipColoc)
    impNoColc = ImagePlus("no coloc", ipNoColoc)
    
    imp1.show()
    imp2.show()
    impRandrois.show()
    impColoc.show()
    impNoColc.show()
    
    
    return
    st = imp.getStatistics()
    totalMean = st.mean
    totalPixel = st.pixelCount

    rows = [[means[i][0], means[i][1], roiPixelCounts[i], totalMean, totalPixel, getQuantile(roiCounts, 0.5), getQuantile(roiCounts, randomRoiQuantile) ] for i in range(len(means))]

    return rows
    

def main():
    
    od = OpenDialog("Select File to analyze")
    if not od.getPath():
        return
    
    rows = spotAnalysisSingle(od.getPath())
    
    

    return
    outFile = od.getPath() + "results.csv"
    outFD = open(outFile, "w")

    outFD.write("\t".join(["spotMean1", "spotMean2" "spotPx", "totalMean", "totalPx", "q50", "q95"]) + "\n")
    
   

    outrows = [rows[i] for i in range(len(rows))]

    for r in outrows:
        outFD.write("\t".join(map(str, r)) + "\n")

    
    outFD.close()
    print "DONE"
    
    
    
    
if __name__ == "__main__":
    main()