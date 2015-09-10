from ij.gui import GenericDialog
from ij.io import DirectoryChooser

dc = DirectoryChooser("Choose directory to process")
startingDir = dc.getDirectory()

gd = GenericDialog("Options")
gd.addStringField("Pattern:", "")
gd.addCheckboxGroup(2,1, ["RGB", "composite"], [True, True], ["Output format"])
gd.showDialog()

pattern = gd.getNextString()
doRGB = gd.getNextBoolean()
doComposite = gd.getNextBoolean()

print(pattern)

def impToComposite(imp, channelOrder = [2, 1, 0]):
    pass
    
def impToRGB(imp, channelOrder = [2, 1, 0]):
    pass