#	Convert Micromanager output files (one file per angle, multiple channels per file)
#	(format: *Pos{a}.ome.tif)
#	to one-file-per-angle-and-channel
#	(format *Pos{a}_Channel{c}.ome.tif)
#	saved in folder named "convert"

from ij import IJ;
from ij import ImagePlus;
from ij import ImageStack;
from ij import ImageJ
from ij.process import ImageProcessor;
from ij.io import DirectoryChooser

import os.path;
import os;
import glob;
import sys

### USER INPUT

# input directory goes here
#inputDir = "/Users/david/Desktop/F_tet_4_1";
dc = DirectoryChooser("Choose directory to process!")
inputDir = dc.getDirectory()
# set to True if you want to process all subdirectories of input
# or False if you only want to process the one input dir
processSubdirs = True;
# subdirectories to be ignored
ignoreDirectories = ["488", "562", "convert", "mv-workspace"]

### END USER INPUT

def splitChannelsForMV(path):

	if not path.endswith(os.sep):
		path += os.sep;

	# create output directory
	if not os.path.exists(path + "mv-workspace"):
		os.makedirs(path + "mv-workspace");

	if os.path.exists(os.path.join(path, "mv-workspace", "0SPLITDONE")):
		print("Already processed that dir. To redo it, delete the OSPLITDONE file!")
		return

	# get all image files (*.ome.tif)
	imageFiles = glob.glob(path + "*.ome.tif");
	#print(imageFiles);

	for f in imageFiles:
		img = IJ.openImage(f);
		#img.show();

		# create new Stack for each channel
		channelStacks = [];
		nChannels = img.getNChannels();
		for i in range(nChannels):
			channelStacks.append(img.createEmptyStack());

		# print(img.getNSlices());
		for i in range (1, img.getNSlices() + 1):
			for j in range(1, nChannels+1):
				img.setC(j);
				img.setZ(i);
				channelStacks[j-1].addSlice(img.getProcessor());

		channelImgs = [];
		for i in range(1, nChannels + 1):
			channelImgs.append(ImagePlus("channel " + str(i), channelStacks[i-1]));


		for i in range(1, nChannels + 1):
			(h, t) =  os.path.split(f);
			newFile = h + "/mv-workspace/" + t.split(".ome.tif")[0] + "_Channel" + str(i) + ".ome.tif"

			print("saving: " + newFile);
			IJ.saveAsTiff(channelImgs[i-1] , newFile);

	open(os.path.join(path, "mv-workspace", "0SPLITDONE"), 'a').close()

def anyEndsWith(strings, suffix):
	'''
	check wether any of the strings in strings ends with a suffix
	'''
	for s in strings:
		if s.endswith(suffix):
			return True
	return False



### main()
## handle subdirs
if processSubdirs:

	dirs = os.walk(inputDir)
	sdirs = list()

	for d in dirs:
		skip = False
		for di in ignoreDirectories:
			if di in d[0].split(os.sep):
				skip = True
		if skip: continue
		if anyEndsWith(d[2], ".ome.tif"):
			sdirs.append(d[0])

	print("-- Handling multiple input directories:");
	for i in sdirs:
		print("- Handing dir: " + i);
		splitChannelsForMV(i);

## handle only one directory
else:
	print("-- Handling one input directory: " + inputDir);
	splitChannelsForMV(inputDir);

print("Finished.");

sys.exit()
