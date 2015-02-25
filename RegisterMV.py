'''
@author: david
'''

from ij import IJ;
from ij.io import DirectoryChooser

import os.path;
import os;
import re
import sys

### USER INPUT

# input directory goes here
#inputDir = "/Users/david/Desktop/F_tet_4_1";
dc = DirectoryChooser("Choose directory to process!")
inputDir = dc.getDirectory()
# set to True if you want to process all subdirectories of input
# or False if you only want to process the one input dir
processSubdirs = True;

xdist = ".650"
ydist = ".650"
zdist = "6"

channelWithBeads = "1"

radius1 = "1"
radius2 = "2"
threshold = ".005"

### END USER INPUT

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

sys.exit()