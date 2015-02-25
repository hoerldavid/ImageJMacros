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

#channelsToFuse = [1,2]
channelsToDeconvolve = [1]

downsample=1
nIterations = 1

### END USER Input

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
    deconvolveCmd = ("browse="+os.path.join(path, "dataset.xml") +
                    " select_xml="+os.path.join(path, "dataset.xml")+
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

sys.exit()
