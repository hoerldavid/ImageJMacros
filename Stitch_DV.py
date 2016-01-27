'''
Splitting and stitching of .dv (pDV) panel image acquisitions

David Hoerl,
started 12.5.2015
'''

from java.lang import Short, Class
from java.awt.Color import RED, GREEN, BLUE
from java.util.prefs import Preferences

from jarray import array

from ij.gui import GenericDialog
from ij.io import DirectoryChooser
from ij import IJ, ImageJ
from ij.process import StackConverter, LUT
from ij.plugin import ChannelArranger
from ij.plugin import Concatenator, HyperStackConverter

from loci.plugins import BF

from math import ceil

# manually import ImporterOptions, as the package name contains the "in" constant
ImporterOptions = __import__("loci.plugins.in.ImporterOptions", globals(), locals(), ['object'], -1)

import os
import re

def getParametersFromLog(file, deconvBorder):
    '''
    determine the number of tiles and their arrangement from pDV log files
    also determine rolloff (%)
    deconvolution cuts off border from raw images,
    pass the number of cut pixels in each dimension to compensate (calculate rolloff correctly)
    '''
    fd = open(file, "r")
    
    xCoords = set()
    yCoords = set()
    width = 0
    height = 0
    rolloff = 0
    
    panelSep = 0
    pixelSizeX = 0
    
    pStageCoords = re.compile(".*?\((.*?),(.*?),(.*?)\).*?")
    pXYDim = re.compile(".*?([0-9]*) x ([0-9]*).*?")
    for line in fd:
        if ("Stage coordinates" in line):
            m = pStageCoords.match(line)
            xCoords.add(m.groups()[0])
            yCoords.add(m.groups()[1])
#        elif ("OVERLAP" in line):
#            rolloff = int(line.split(" ")[-1].strip())
        elif ("XY Dimensions" in line):
            m = pXYDim.match(line)
            width = int(m.groups()[0])
            height = int(m.groups()[1])
            
        elif ("Pixel Size" in line):
            pixelSizeX = float(line.split()[2])
            #print(line.split())
            
        elif("PANEL_SEPARATION" in line):
            panelSep = abs(float(line.split(" ")[-1]))
            #print(panelSep)
            
            
    return((len(xCoords), len(yCoords)), (panelSep - pixelSizeX * deconvBorder)/((width - deconvBorder) * pixelSizeX))
    #return(map(float, xCoords), map(float, yCoords))


def changeChannelOrder(imp, channelOrder = [3,2,1]):
    '''
    change the order of channels in a multicolor ImagePlus
    default rearrangement: (red, green, blue) -> (blue, green, red)
    '''
    return ChannelArranger.run(imp, array(channelOrder, 'i'))
    
def changeLUTOrder(imp, channelOrder=[3, 2, 1]):
    luts = imp.getLuts()
    newLuts = [luts[i-1] for i in channelOrder]
    imp.setLuts(newLuts)

def importTiles(path):
    '''
    open DV file as created by the tile acquisition
    return single imps (composite colors)
    '''

    imps = None
    try:
        io = ImporterOptions()
        io.setId(path)
        io.setOpenAllSeries(True)
        io.setSplitTimepoints(True)
        io.setColorMode(ImporterOptions.COLOR_MODE_COMPOSITE)
        
        imps = BF.openImagePlus(io)    
    except Exception, e:
        print(e)
        IJ.log("ERROR while opening image file " + path)
    
    return imps

def correctSigned16Bit(imp):
    '''
    correct a signed 16bit image that is interpreted as an unsigned 16bit image (2^15-2^16) 
    to (0 - 2^15-1) by subtracting the maximum signed value (2^15-1)
    '''
    for c in range(1,imp.getNChannels()+1):
        for s in range(1, imp.getNSlices()+1):
            for f in range(1, imp.getNFrames()+1):
                imp.setPosition(c, s, f)
                imp.getProcessor().add(-Short.MAX_VALUE)

def makeHyperstack(path, channelOrder = [3,2,1]):
    imps = []
    p = re.compile("img_t[0-9]+_z[0-9]+_c[0-9]+")
    for f in [fi for fi in (os.walk(path).next()[2]) if p.match(fi)]:
        #print(f)
        imps.append(IJ.openImage(os.path.join(path, f)))
        
    c = Concatenator()
    res = c.concatenateHyperstacks(imps, path, False)
    res2 = HyperStackConverter.toHyperStack(res, len(channelOrder), len(imps)/len(channelOrder), 1)
    changeLUTOrder(res2, channelOrder)
    return res2

def getChannelMinAndMax(imps):
    accu = []
    for imp in imps:
        for c in range(1,imp.getNChannels()+1):
            imp.setC(c)
            # create empty minmax arrays in first iteration
            if len(accu) < c:
                accu.append([])
            for z in range(1,imp.getNSlices()+1):
                imp.setZ(z)
                st = imp.getStatistics()
                accu[c-1].append((st.min, st.max))
            
    res = []
    for mmax in accu:
        res.append(reduce(lambda x,y: (min(x[0], y[0]), max(x[1], y[1])), mmax))
        
    return res
    
    
def main():
    
    # minimal rolloff = 0%?
    minRolloff = 0
    
    prefs = Preferences.userRoot()
    
    DO_SPLIT_KEY = "DO_SPLIT"
    DO_STITCH_KEY = "DO_STITCH"
#    DO_SINGLEFILE_KEY = "DO_SINGLEFILE"
    CHANNEL_ORDER_KEY = "CHANNEL_ORDER"
    PATTERN_KEY = "PATTERN"
#    TILE_CONFIG_KEY = "TILE_CONFIG"
    DUMMY_KEY = "DUMMY_STITCHING"
    DECONV_BORDER_KEY = "DECONV_BORDER"
    
    
    # ----------- DEFAULT VALUES FOR USER INPUT --------------    
    DO_SPLIT_DEF = True
    DO_STITCH_DEF = True
#    DO_SINGLEFILE_DEF = True
    CHANNEL_ORDER_DEF = "3,2,1"
    PATTERN_DEF = "_D3D.dv"
#    TILE_CONFIG_DEF = "4x4"
    DUMMY_DEF = False
    DECONV_BORDER_DEF = "64"
    
    # get earlier values, if they exist
    doSplit = prefs.getBoolean(DO_SPLIT_KEY, DO_SPLIT_DEF)
    doStitch = prefs.getBoolean(DO_STITCH_KEY, DO_STITCH_DEF)
#    doSingleFile = prefs.getBoolean(DO_SINGLEFILE_KEY, DO_SINGLEFILE_DEF)    
    pattern = prefs.get(PATTERN_KEY, PATTERN_DEF)
    channelOrder = prefs.get(CHANNEL_ORDER_KEY, CHANNEL_ORDER_DEF)
#    tileConf = prefs.get(TILE_CONFIG_KEY, TILE_CONFIG_DEF)  
    dummyStitching = prefs.getBoolean(DUMMY_KEY, DUMMY_DEF)
    deconvBorder = prefs.get(DECONV_BORDER_KEY, DECONV_BORDER_DEF)
    
    
    dc = DirectoryChooser("Pick directory to process.")
    startingDir = dc.getDirectory()
    
    gd = GenericDialog("Set Options")
    gd.addCheckbox("split .dv file into tiles?", doSplit)
    gd.addStringField("pattern (only process files that end with that)", pattern)
    gd.addStringField("order of channel colors (1=red, 2=green 3=blue)", channelOrder)
    gd.addCheckbox("stitch the split tiles?", doStitch)
    gd.addCheckbox("dummy stitching (no overlap calculation)", dummyStitching)
    gd.addStringField("deconvolution border (px)", deconvBorder)
#    gd.addStringField("Tile Configuration", tileConf)
#    gd.addCheckbox("Do Single File?", doSingleFile)
    
    gd.showDialog()
    
    if (gd.wasCanceled()):
        return
    
    
    doSplit = gd.getNextBoolean()
    
    pattern = str(gd.getNextString())
    channelOrder = str(gd.getNextString())
    channelOrderInt = map(int, map(str.strip, channelOrder.split(",")))
    #print(channelOrderInt)
    
    doStitch = gd.getNextBoolean()
#    tileConf = str(gd.getNextString())
#    doSingleFile = gd.getNextBoolean()
    dummyStitching = gd.getNextBoolean()
    deconvBorder = gd.getNextString()
    
    # save last user input
    prefs.putBoolean(DO_SPLIT_KEY, doSplit)
    prefs.putBoolean(DO_STITCH_KEY, doStitch)
#    prefs.putBoolean(DO_SINGLEFILE_KEY, doSingleFile)
    
    prefs.put(PATTERN_KEY, pattern)
    prefs.put(CHANNEL_ORDER_KEY, channelOrder)
    prefs.putBoolean(DUMMY_KEY, dummyStitching)
    prefs.put(DECONV_BORDER_KEY, deconvBorder)
#    prefs.put(TILE_CONFIG_KEY, tileConf) 

    ### get int value of deconvBorder
    deconvBorder = int(deconvBorder)
    
    IJ.log("--- STITCHING STARTED ---")
    
    nFiles = 0
    for (p, d, f) in os.walk(startingDir):
        for fi in f:
            if fi.endswith(pattern):
                IJ.log("will process file: " + os.path.join(p, fi))
                nFiles += 1
    
    
    doneFiles = 0
    for (p, d, f) in os.walk(startingDir):
        for fi in f:
            if fi.endswith(pattern):
                
                inFile = os.path.join(p,fi)

                outDir = inFile + "_SPLIT"
                if doSplit:
                    IJ.log("-- SPLITTING: " + inFile)
                    
                    
                    #print(inFile)
                    imps = importTiles(inFile)
                    #print(imps[0].getLuts())
                    
                    # create output directory
                    if not os.path.exists(outDir):
                        os.makedirs(outDir)
                        
                    for i in range(len(imps)):
                        # to 32bit -> no ambiguous signed/unsigned values
                        #StackConverter(imps[i]).convertToGray32()
                        #imps[i].show()
                        #imps[i] = changeChannelOrder(imps[i], channelOrderInt)
                        #changeLUTOrder(imps[i], channelOrderInt)
                        #outImp.show()
                        #correctSigned16Bit(imps[i])
                        pass
                    
                    levels = getChannelMinAndMax(imps)

                    print levels
                    
                    
                    for i in range(len(imps)):
                        
                        #imp = imps[i]
                        imps[i].show()
                        IJ.selectWindow(imps[i].getID())
                        #IJ.saveAsTiff(imps[i], os.path.join(outDir, "tile" + str(i) + ".tif"))
                        for c in range(1,imps[i].getNChannels()+1):
                            imps[i].setC(c)
                            IJ.runMacro("setMinAndMax("+str(int((levels[c-1][0])))+","+str(int((levels[c-1][1])))+");")
                            #imps[i].setDisplayRange(levels[c-1][0], levels[c-1][1])                        
                        #IJ.saveAsTiff(imps[i], os.path.join(outDir, "tile" + str(i) + "_leveled.tif"))
                        StackConverter(imps[i]).convertToRGB()
                        IJ.saveAsTiff(imps[i], os.path.join(outDir, "tile" + str(i) + "_leveled_rgb.tif"))
                        imps[i].close()    

                    
                if doStitch:
                    IJ.log("-- STITCHING: " + inFile)
                    #tiles = tileConf.split("x")
                    
                    logFile = inFile[:inFile.find(pattern)] + ".dv.log"
                    if not os.path.exists(logFile):
                        IJ.log("ERROR: could not find log file for file: "+ inFile)
                    
                    #deconvBorder = 64
                    ((xtiles, ytiles), rolloff) = getParametersFromLog(logFile, deconvBorder)
                    
                    # create stitching output directory
                    stitchDir = inFile + "_STITCHED"
                    if not os.path.exists(stitchDir):
                        os.makedirs(stitchDir)
                        
                    # check that rolloff is at least a minimum value (1% at the moment)
                    # TODO: integer cast necessary here
                    overlapPercent = (rolloff*100) if (rolloff*100) > minRolloff else minRolloff

                    print overlapPercent
                    #overlapPercent = 3.5
                    
                    stitchCmd = "Grid/Collection stitching"
                    
                    #dummyStitching = True
                    
                    # real stitching with overlap calculation
                    if not dummyStitching:
                        stitchOptions = ('''type=[Grid: snake by rows] order=[Right & Down                ]
                                         grid_size_x='''+str(xtiles)+''' grid_size_y='''+str(ytiles)+" tile_overlap="+ str(overlapPercent)+
                                         ''' first_file_index_i=0 directory=[''' +
                                         outDir + '''] file_names=tile{i}_leveled_rgb.tif output_textfile_name=TileConfiguration.txt 
                                         fusion_method=[Linear Blending] regression_threshold=0.30 
                                         max/avg_displacement_threshold=2.50 absolute_displacement_threshold=3.50 
                                         compute_overlap subpixel_accuracy computation_parameters=[Save computation time (but use more RAM)] 
                                         image_output=[Fuse and display]''')
                                         
                    # dummy stitching -> fuse tiles based on configuration and overlap
                    else:                     
                        stitchOptions = ('''type=[Grid: snake by rows] order=[Right & Down                ]
                                         grid_size_x='''+str(xtiles)+''' grid_size_y='''+str(ytiles)+" tile_overlap="+ str(overlapPercent)+
                                         ''' first_file_index_i=0 directory=[''' +
                                         outDir + '''] file_names=tile{i}_leveled_rgb.tif output_textfile_name=TileConfiguration.txt 
                                         fusion_method=[Linear Blending] regression_threshold=0.30 
                                         max/avg_displacement_threshold=2.50 absolute_displacement_threshold=3.50 
                                         subpixel_accuracy computation_parameters=[Save computation time (but use more RAM)] 
                                         image_output=[Fuse and display]''')
                                         
                    
                    IJ.run(stitchCmd, stitchOptions)
                    
                    outFile = os.path.join(inFile + "_STITCHED", "stitched.tif")
                    imp = IJ.getImage()
                    changeLUTOrder(imp, channelOrderInt)

                    levels = getChannelMinAndMax([imp])
                    for c in range(1,imp.getNChannels()+1):
                        imp.setC(c)
                        IJ.runMacro("setMinAndMax("+str(int((levels[c-1][0])))+","+str(int((levels[c-1][1])))+");")
                    
                    IJ.saveAsTiff(imp, outFile)
                    imp.close()
                    
#                 if doSingleFile:
#                     IJ.log("-- MERGING: " + inFile)
#                     imp = makeHyperstack(inFile + "_STITCHED", channelOrderInt)
#                     #imp.show()
#                     IJ.saveAsTiff(imp, os.path.join(inFile + "_STITCHED", "stitched.tif"))
                    
                doneFiles += 1
                IJ.log("finished file "+str(doneFiles)+" of "+str(nFiles))

if __name__ == "__main__":
    main()
