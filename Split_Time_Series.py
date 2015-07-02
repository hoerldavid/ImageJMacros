import os
import re
import sys
import gc

from ij import IJ
from ij import ImagePlus
from ij import ImageStack
from ij import ImageJ
from ij.process import ImageProcessor
from ij.io import DirectoryChooser
from ij.gui import GenericDialog

# --------------------------------
# Set defaults here:
slicesPerTimepointDefault = 51
nChannelsDefault = 2
# --------------------------------

def main():
    '''
    split MicroManager md-Acquisition result files into timepoints and channels
    will handle files that were split due to large size
    '''

    # let the user selct number of channels, slices per tp
    gd = GenericDialog("Specify settings for split")
    gd.addStringField("slices per timepoint", str(slicesPerTimepointDefault))
    gd.addStringField("number of channels", str(nChannelsDefault))
    gd.showDialog()
    
    if gd.wasCanceled():
        return
    
    slicesPerTimePoint = int(gd.getNextString())
    nChannels = int(gd.getNextString())
    
    
    # let user select directory, use only this directory (not subdirectories)
    dc = DirectoryChooser("Choose directory to process.")
    inputPath = dc.getDirectory()
    
    dirs = os.walk(inputPath)
    inputDir = dirs.next()
    
    
    # make output dir
    if not os.path.exists(os.path.join(inputPath, "timepoints")):
        os.makedirs(os.path.join(inputPath, "timepoints"))
    
    # pattern of the image files
    p = re.compile("(.*?Pos[0-9])(.*?\.ome\.tif)")
    
    # map all image file prefixes (corresponding to angles)
    # to all files starting with it (containing the timepoints)
    prefixes = dict()
    
    for f in inputDir[2]:
        m = p.match(f)
        
        # file matches pattern
        if m:
            
            # new prefix
            if not m.groups()[0] in prefixes:
                prefixes[m.groups()[0]] = list()
            
            # add new suffix to dict for prefix  
            prefixes[m.groups()[0]].append(m.groups()[1])

    #print(prefixes.items())
    
    for prefix, suffix in prefixes.items():

        
        
        # open first image to create stacks (copy dimensions etc.)
        firstImg = IJ.openVirtual(os.path.join(inputPath, prefix + suffix[0]))
        
        #make an output Stack for every channel
        #keep track of timepoint for every stack
        tpStacks = []
        tpNrs = []
        for i in range(nChannels):
            tpStacks.append(firstImg.createEmptyStack())
            tpNrs.append(0)
            
                
        chNr = 0
        
        # to deallocate image
        firstImg.close()
        # gc.collect()
        
        # go through all files and append slices to the output stacks
        for s in suffix:

            print("reading image " + prefix + s)
            img = IJ.openVirtual(os.path.join(inputPath, prefix + s))
    
            for i in range(1, img.getImageStackSize()+1):
                        
                
                img.setPosition(i)
                tpStacks[chNr].addSlice(img.getProcessor().duplicate())
                
                # rotate through channels for every slice
                chNr = (chNr + 1)%nChannels
                                    
                for j in range(nChannels):
                    if tpStacks[j].getSize() == slicesPerTimePoint:
                        outImg = ImagePlus("Timepoint " + str(tpNrs[j]) + " Channel " + str(j), tpStacks[j])
                        IJ.saveAsTiff(outImg.duplicate() , os.path.join(inputPath, "timepoints", prefix + "_TP" + str(tpNrs[j]) +"_Channel"+ str(j+1)+ ".ome.tif"))
                        tpStacks[j] = img.createEmptyStack()
                        tpNrs[j] = tpNrs[j] + 1
                        print("wrote channel " + str(j) + " tp " + str(tpNrs[j]) )
    
            # to deallocate image
            img.close()
            #gc.collect()
        
        # save last Timepoint (possibly incomplete)
        for j in range(nChannels):
            if not tpStacks[j].getSize() == 0:
                 outImg = ImagePlus("Timepoint " + str(tpNrs[j]) + " Channel " + str(j), tpStacks[j])
                 IJ.saveAsTiff(outImg , os.path.join(inputPath, "timepoints", prefix + "_TP" + str(tpNrs[j]) +"_Channel"+ str(j+1)+ ".ome.tif"))
                


if __name__ == "__main__":
    main()