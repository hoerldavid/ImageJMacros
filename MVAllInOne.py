from ij import IJ;
from ij import ImagePlus;
from ij import ImageStack;
from ij.process import ImageProcessor;
from ij.io import DirectoryChooser

import os.path;
import os;
import glob;
import re

# input directory goes here
#inputDir = "/Users/david/Desktop/F_tet_4_1";
dc = DirectoryChooser("Choose directory to process!")
inputDir = dc.getDirectory()
# set to True if you want to process all subdirectories of input
# or False if you only want to process the one input dir
processSubdirs = True;
# subdirectories to be ignored
ignoreDirectories = ["488", "561", "562", "convert", "mv-workspace"]

xdist = ".650"
ydist = ".650"
zdist = "6"

channelWithBeads = "1"

radius1 = "1"
radius2 = "2"
threshold = ".005"

#channelsToFuse = [1,2]
channelsToDeconvolve = [1]

downsample=2
nIterations = 1


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

def anyMatches(strings, regex):
	'''
	check wether any of the strings in strings ends with a suffix
	'''
	p = re.compile(regex)
	for s in strings:
		if p.match(s):
			return True
	return False

def registerMV(path):

    if os.path.exists(os.path.join(path, "1REGISTERDONE")):
        print("Already processed that dir. To redo it, delete the 1REGISTERDONE file!")
        return

    files = os.walk(path).next()[2]
    #print(files)

    pref = set()
    posnrs = set()
    chnrs = set()
    p = re.compile("(.*)Pos(\d+)_Channel(\d+)\.ome\.tif")

    for f in files:
        m = p.match(f)
        if m:
            pref.add(m.groups()[0])
            posnrs.add(m.groups()[1])
            chnrs.add(m.groups()[2])

    if len(pref) != 1:
        print("Filenames in this dir don't match. Please name files in the form: *_Pos{a}_Channel{c}.ome.tif")
        return

    filepattern = iter(pref).next() + "Pos{a}_Channel{c}.ome.tif"

    #print(filepattern)
    #print(posnrs)
    #print(chnrs)

    ### DEFINE DATASET
    datadef = "Define Multi-View Dataset"
    commandDatadef = ('''type_of_dataset=[Image Stacks (ImageJ Opener)]
                xml_filename=dataset.xml multiple_timepoints=[NO (one time-point)] multiple_channels=[YES (one file per channel)]
                _____multiple_illumination_directions=[NO (one illumination direction)] multiple_angles=[YES (one file per angle)]
                image_file_directory=''' + path
                + ''' image_file_pattern=''' + filepattern
                + " channels_=" + ",".join(chnrs) + " acquisition_angles_=" + ",".join(posnrs) +
                ''' calibration_type=[Same voxel-size for all views] calibration_definition=[User define voxel-size(s)]
                imglib2_data_container=[ArrayImg (faster)]
                pixel_distance_x=''' + xdist +  " pixel_distance_y=" + ydist + " pixel_distance_z=" + zdist + " pixel_unit=um"
                )

    IJ.run(datadef, commandDatadef)

    ### DETECT INTEREST POINTS
    detectip = "Detect Interest Points for Registration"
    commandDetectIP = ("select_xml=" + os.path.join(path, "dataset.xml") +
                       " process_angle=[All angles] process_illumination=[All illuminations] process_timepoint=[All Timepoints]" +
                       " type_of_interest_point_detection=[Difference-of-Mean (Integral image based)] label_interest_points=beads" +
                       " channel_" + channelWithBeads +" subpixel_localization=[3-dimensional quadratic fit] " +
                       "interest_point_specification_(channel_" + channelWithBeads + ")=[Advanced ...] " +
                       "radius_1="+radius1+" radius_2="+radius2+" threshold="+threshold+" find_maxima"
                       )

    IJ.run(detectip, commandDetectIP)

    ### REGISTER

    register = "Register Dataset based on Interest Points"
    commandRegister = ( "select_xml="+ os.path.join(path, "dataset.xml") +
                        " process_angle=[All angles] process_illumination=[All illuminations] process_timepoint=[All Timepoints]" +
                        " registration_algorithm=[Fast 3d geometric hashing (rotation invariant)] " +
                        "type_of_registration=[Register timepoints individually] interest_points_channel_1=beads " +
                        "interest_points_channel_2=[[DO NOT register this channel]] fix_tiles=[Fix first tile] " +
                        "map_back_tiles=[Do not map back (use this if tiles are fixed)] "+
                        "transformation=Affine allowed_error_for_ransac=5"
                        )

    IJ.run(register, commandRegister)

    ### COPY REGISTRATION TO ALL CHANNELS

    dupTransform = "Duplicate Transformations"
    commandDupTransform = ("apply=[One channel to other channels]"+
                           " select_xml="+ os.path.join(path, "dataset.xml") +
                           " apply_to_angle=[All angles] apply_to_illumination=[All illuminations] "+
                           "apply_to_timepoint=[All Timepoints] source=1 target=[All Channels] "+
                           "duplicate_which_transformations=[Replace all transformations]" )

    IJ.run(dupTransform, commandDupTransform)


    open(os.path.join(path, "1REGISTERDONE"), 'a').close()


def fuseAllChannels(path):
    fuse = "Fuse/Deconvolve Dataset"
    fuseCmd = ( "select_xml="+ os.path.join(path, "dataset.xml") +
                " process_angle=[All angles] process_channel=[All channels] " +
                "process_illumination=[All illuminations] process_timepoint=[All Timepoints] "+
                "type_of_image_fusion=[Weighted-average fusion]"+
                " bounding_box=[Estimate automatically (experimental)] fused_image=[Save as TIFF stack] "+
                "downsample=" + str(downsample) +" pixel_type=[32-bit floating point] imglib2_container=ArrayImg "+
                "process_views_in_paralell=All blend interpolation=[Linear Interpolation] "+
                "output_file_directory=" + os.path.join(path, "") )

    IJ.run(fuse, fuseCmd)


def deconvolveChannel(path, channel):
    deconvolve = "Fuse/Deconvolve Dataset"
    deconvolveCmd = ( "select_xml="+os.path.join(path, "dataset.xml")+
                    " process_angle=[All angles] process_channel=[Single channel (Select from List)]"+
                    " process_illumination=[All illuminations] process_timepoint=[All Timepoints] "+
                    " processing_channel=[channel "+str(channel)+"] type_of_image_fusion=[Multi-view deconvolution]"+
                    " bounding_box=[Estimate automatically (experimental)] "+
                    "fused_image=[Save as TIFF stack] "+
                    "imglib2_container=ArrayImg type_of_iteration="+
                    "[Efficient Bayesian - Optimization I (fast, precise)] "+
                    "osem_acceleration=[1 (balanced)] number_of_iterations="+str(nIterations)+
                    " use_tikhonov_regularization tikhonov_parameter=0.0060 "+
                    "compute=[in 512x512x512 blocks] compute_on=[GPU (Nvidia CUDA via JNA)] "+
                    "psf_estimation=[Extract from beads] psf_display=[Do not show PSFs] "+
                    "output_file_directory="+path+
                    " directory=/opt/Fiji.app/lib/linux64 " +
                    "select_native_library_for_cudafourierconvolution=FourierConvolutionCUDALib.so gpu_1"+
                    " detections_to_extract_psf_for_channel_1=beads psf_size_x=19 psf_size_y=19 psf_size_z=25"
                    )

    IJ.run(deconvolve, deconvolveCmd)

def fuseMV(path):
    if os.path.exists(os.path.join(path, "2FUSEDONE")):
        print("Already processed that dir. To redo it, delete the 2FUSEDONE file!")
        return

    fuseAllChannels(path)

    for ch in channelsToDeconvolve:
        # TODO change to deconvolution
        deconvolveChannel(path, ch)


    open(os.path.join(path, "2FUSEDONE"), 'a').close()



#### CHANNEL SPLITTING

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
		if anyMatches(d[2], ".*Pos\d+\.ome\.tif"):
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


##### REGISTRATION

### main()
## handle subdirs
if processSubdirs:

    dirs = os.walk(inputDir)
    sdirs = list()

    for d in dirs:
        if d[0].endswith("mv-workspace"):
            sdirs.append(d[0])

    print("-- Handling multiple input directories:");
    for i in sdirs:
        print("- Handing dir: " + i);
        registerMV(i);

## handle only one directory
else:
    print("-- Handling one input directory: " + inputDir);
    registerMV(inputDir);

print("Finished.");

##### FUSION

### main()
## handle subdirs
if processSubdirs:

    dirs = os.walk(inputDir)
    sdirs = list()

    for d in dirs:
        if d[0].endswith("mv-workspace"):
            sdirs.append(d[0])

    print("-- Handling multiple input directories:");
    for i in sdirs:
        print("- Handing dir: " + i);
        fuseMV(i);

## handle only one directory
else:
    print("-- Handling one input directory: " + inputDir);
    fuseMV(inputDir);

print("Finished.");
