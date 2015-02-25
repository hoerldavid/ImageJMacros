'''
mask of segmented cells + mask of segmented particles (chromocenters) + raw image
--> CSV of statistics with corresponding cells, particles

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

import os.path, os
import csv
import re
import sys


# Particle analyzer settings
minCellSize = 3000
minFeatureSize = 150
minCircularity = 0.25

# TODO: stanard output doesn't give us anything but count, minmax, mean
desiredMeasurements = Measurements.MEAN + Measurements.MIN_MAX


# open segmentation result files
dc1 = OpenDialog("Select cell segmentation results")
fileSegmentedCells = os.path.join(dc1.getDirectory(), dc1.getFileName())

dc2 = OpenDialog("Select feature segmentation results")
fileSegmentedFeatures = os.path.join(dc2.getDirectory(), dc2.getFileName())

# open raw image file
dc3 = OpenDialog("Select file to analyze")
fileData = os.path.join(dc3.getDirectory(), dc3.getFileName())

imageSegmentedCells = IJ.openImage(fileSegmentedCells)
imageSegmentedFeatures = IJ.openImage(fileSegmentedFeatures)
imageData = IJ.openImage(fileData)


nSlices = imageSegmentedCells.getNSlices()

rm = RoiManager()

# find cells, save rois in cellRois (list containing a list of rois for each slice)
cellRois = list()
for i in range(1,nSlices+1):
    
    imageSegmentedCells.setSlice(i)
    
    # particle analyzer wants a results table
    rtCells = ResultsTable()
    paCells = ParticleAnalyzer(ParticleAnalyzer.ADD_TO_MANAGER , 0 , rtCells, minCellSize, Integer.MAX_VALUE, minCircularity, 1.0)
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
        paCells = ParticleAnalyzer(ParticleAnalyzer.ADD_TO_MANAGER , 0 , rtCells, minFeatureSize, Integer.MAX_VALUE, minCircularity, 1.0)
        paCells.analyze(imageSegmentedFeatures)
        
        particleRois[i].append(rm.getRoisAsArray())
        print("found " + str(len(particleRois[i][j])) + " particles in cell " + str(j) +" in slice " + str(i))
        
        imageSegmentedFeatures.killRoi()
        rm.deselect()
        rm.reset()
        
# show example results
# imageSegmentedFeatures.show()
# 
# sliceToShow = 10
# cellToShow = 0
# 
# imageSegmentedFeatures.setSlice(sliceToShow)
# 
# #first roi in manager --> cell
# rm.add(imageSegmentedFeatures, cellRois[sliceToShow][cellToShow], 0)
# 
# # other rois --> particles
# for i in range(len(particleRois[sliceToShow][cellToShow])):
#     rm.add(imageSegmentedFeatures, particleRois[sliceToShow][cellToShow][i], 0)
    
# print(imageSegmentedFeatures.getStatistics().toString())
# rm.select(0)
# print(imageSegmentedFeatures.getStatistics().toString())

def statisticsStringToCSV(statStr):
    '''
    get dict from ImageStatistics.toString()
    '''
    p = re.compile("[a-z]+=[0-9\.]+")
    names = list()
    vals = dict()
    # iterate over all name=value pairs in string
    for st in p.findall(statStr):
        names.append(st.split("=")[0])
        vals[st.split("=")[0]] = st.split("=")[1].replace(".", ",")
        
    return (names, vals)
    
# statisticsStringToCSV(imageSegmentedFeatures.getStatistics().toString())

cellCSVFile = fileData + "_cells.csv"
particles = fileData + "_particles.csv"

csvfile = open(cellCSVFile, "w")
writer = None

# statistics for all cells
for i in range(nSlices):
    imageData.setSlice(i + 1)
    for j in range(len(cellRois[i])):
        
        imageData.setRoi(cellRois[i][j])
        fieldnames, row = statisticsStringToCSV(imageData.getStatistics().toString())
#         print(imageData.getStatistics().stdDev)
        imageData.killRoi()
        
        fieldnames = ["slice", "cell"] + fieldnames
        row["slice"] = str(i)
        row["cell"] = str(j)        
        
        if not writer:
            writer = csv.DictWriter(csvfile, delimiter=";", lineterminator="\r", fieldnames=fieldnames)
            writer.writerow(dict(zip(row.keys(), row.keys())))
#             writer.writeheader()
        
        writer.writerow(row)
     
csvfile.close()

# statistics for all particles

csvfile = open(particles, "w")
writer = None

for i in range(nSlices):
    imageData.setSlice(i + 1)
    for j in range(len(particleRois[i])):
        for k in range(len(particleRois[i][j])):
        
            imageData.setRoi(particleRois[i][j][k])
            fieldnames, row = statisticsStringToCSV(imageData.getStatistics().toString())
            imageData.killRoi()
            
            imageData.setRoi(cellRois[i][j])
            
            fieldnames = ["slice", "cell", "particle", "cell_mean"] + fieldnames
            row["slice"] = str(i)
            row["cell"] = str(j)        
            row["particle"] = str(k)
            row["cell_mean"] = str(imageData.getStatistics().mean)
            
            imageData.killRoi()
            
            if not writer:
                writer = csv.DictWriter(csvfile, delimiter=";", lineterminator="\r", fieldnames=fieldnames)
                writer.writerow(dict(zip(row.keys(), row.keys())))
    #             writer.writeheader()
            
            writer.writerow(row)
     
csvfile.close()
sys.exit()
