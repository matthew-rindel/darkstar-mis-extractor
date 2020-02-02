import glob
import sys
import struct

knownTags = {
    b"HERC",
    b"TANK",
    b"FLYR"
}

persistentFormat = "<4s2L"

importFilenames = []

for importFilename in sys.argv[1:]:
    files = glob.glob(importFilename)
    importFilenames.extend(files)

for importFilename in importFilenames:
    try:
        filenameWithoutExtension = importFilename.replace(".rec", "").replace(".REC", "")

        with open(importFilename, "rb") as recording:
            startIndex = 0
            numberOfVehicles = 0
            rawData = recording.read()
            totalSize = len(rawData)
            while startIndex < totalSize:
                currentIndex = startIndex
                for tag in knownTags:
                    tagOffset = rawData.find(tag, startIndex)
                    if tagOffset != -1:
                        header = struct.unpack_from(persistentFormat, rawData, tagOffset)
                        if header[0] == tag and header[1] < totalSize and header[2] < 10:
                            startIndex = tagOffset + struct.calcsize(persistentFormat) + header[1]
                            vehBytes = bytearray(rawData[tagOffset:tagOffset + header[1] + struct.calcsize(persistentFormat)])
                            print("extracting " + filenameWithoutExtension + "-" + str(numberOfVehicles) + ".veh")
                            with open(filenameWithoutExtension + "-" + str(numberOfVehicles) + ".veh", "wb") as vehicleFile:
                                vehicleFile.write(vehBytes)
                            numberOfVehicles += 1

                if currentIndex == startIndex:
                    startIndex += struct.calcsize(persistentFormat)
    except Exception as e:
        print(e)

