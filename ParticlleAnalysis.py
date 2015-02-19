'''
Created on 19.02.2015

@author: David
'''

from ij import IJ
from ij import ImagePlus
from ij.process import ImageProcessor
from ij.measure import ResultsTable, Measurements
from ij.plugin.filter import ParticleAnalyzer
from ij.plugin.frame import RoiManager

from ij.io import OpenDialog
from java.lang import Integer

import os.path


# Particle analyzer settings
minCellSize = 2000
minFeatureSize = 10


# open segmentation result files
dc1 = OpenDialog("Select cell segmentation results")
fileSegmentedCells = os.path.join(dc1.getDirectory(), dc1.getFileName())

dc2 = OpenDialog("Select feature segmentation results")
fileSegmentedFeatures = os.path.join(dc2.getDirectory(), dc2.getFileName())

imageSegmentedCells = IJ.openImage(fileSegmentedCells)
imageSegmentedFeatures = IJ.openImage(fileSegmentedFeatures)


nSlices = imageSegmentedCells.getNSlices()
# print(nSlices)

rm = RoiManager()

# find cells, save rois in cellRois (list containing a list of rois for each slice)
cellRois = list()
for i in range(1,nSlices+1):
    
    imageSegmentedCells.setSlice(i)
    
    # particle analyzer wants a results table
    rtCells = ResultsTable()
    paCells = ParticleAnalyzer(ParticleAnalyzer.ADD_TO_MANAGER , 0 , rtCells, minCellSize, Integer.MAX_VALUE)
    paCells.analyze(imageSegmentedCells)

    # save rois to list
    cellRois.append(rm.getRoisAsArray())
    print("found " + str(len(cellRois[i-1])) + " cells in slice " + str(i))
    
    # remove rois from manager
    rm.deselect()
    rm.reset()
    
    
# find particles/features in cells, gnerate list (slice) of lists (cells) of lists (particle) of rois
# --> particleRois[slice][cell][particle]     
particleRois = list()

for i in range(nSlices):
    imageSegmentedFeatures.setSlice(i+1)
    particleRois.append(list())
    for j in range(len(cellRois[i])):
        
        imageSegmentedFeatures.setRoi(cellRois[i][j])
        rm.select(imageSegmentedFeatures, 0)
        
        rtCells = ResultsTable()
        paCells = ParticleAnalyzer(ParticleAnalyzer.ADD_TO_MANAGER , 0 , rtCells, minFeatureSize,4000)
        paCells.analyze(imageSegmentedFeatures)
        
        particleRois[i].append(rm.getRoisAsArray())
        print("found " + str(len(particleRois[i][j])) + " particles in cell " + str(j) +" in slice " + str(i))
        
        imageSegmentedFeatures.killRoi()
        rm.deselect()
        rm.reset()
        
# show example results
imageSegmentedFeatures.show()

sliceToShow = 10
cellToShow = 0

imageSegmentedFeatures.setSlice(sliceToShow)

#first roi in manager --> cell
rm.add(imageSegmentedFeatures, cellRois[sliceToShow][cellToShow], 0)

# other rois --> particles
for i in range(len(particleRois[sliceToShow][cellToShow])):
    rm.add(imageSegmentedFeatures, particleRois[sliceToShow][cellToShow][i], 0)
        