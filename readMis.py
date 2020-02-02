from collections import namedtuple
import struct
import json
import sys

importFilenames = sys.argv[1:]

with open(importFilenames[0], "rb") as input_fd:
    rawData = input_fd.read()

knownTags = {
    b"SIMG",
    b"SVol",
    b"ESpt",
	b"STER",
	b"SKYT",
	b"SKPL",
    b"SKSF",
    b"HERC",
    b"TANK",
    b"TRRT",
	b"FLYR",
	b"ESNM",
    b"ESDP",
    b"SCPG",
    b"Ssgp",
    b"\x00\x01\x00\x00",
    b"\x0c\x01\x00\x00",
    b"\x00\x00\x00\x0c",
    b"DPNT",
    b"trgr",
	b"mark",
    b"SNOW"
}

def readGroupString(rawData, offset, index, length):
    (offset, result) = readString(rawData, offset, index != length - 1)

    if (index == 0 and result == ""):
        (offset, result) = readString(rawData, offset, index != length - 1)
    return (offset, result)

def readString(rawData, offset, seekExtra = True):
    stringStruct = "<B"
    terminatorStruct = "<s"
    (length, ) = struct.unpack_from(stringStruct, rawData, offset)
    if length > 25:
        return (offset, "")

    offset += struct.calcsize(stringStruct)
    if length == 0:
        return (offset, "")

    finalStruct = "<" + str(length) + "s"
    (someString,) = struct.unpack_from(finalStruct, rawData, offset)

    offset += struct.calcsize(finalStruct)

    if offset != len(rawData) and seekExtra is True:
        (terminator, ) = struct.unpack_from(terminatorStruct, rawData, offset)

        while (terminator == b"\0"):
            offset += struct.calcsize(terminatorStruct)
            (terminator,) = struct.unpack_from(terminatorStruct, rawData, offset)

    return (offset, someString)


object = "<4s2L"

def readSimVol(objectTypes, rawData, offset):
    simVol = "<4s7L"
    header = struct.unpack_from(simVol, rawData, offset)
    offset += struct.calcsize(simVol)
    (offset, volumeString) = readString(rawData, offset)
    print(b"SimVol in use is " + volumeString)
    return (offset, volumeString)

def readSimGroup(objectTypes, rawData, offset):
    simGroup = "<4s3L"
    header = struct.unpack_from(simGroup, rawData, offset)

    offset += struct.calcsize(simGroup)
    children = []
    finalChildren = {}
    i = 0
    while i < header[-1]:
        objectInfo = struct.unpack_from(object, rawData, offset)
        if (objectInfo[0] not in knownTags):
            currentTag = objectInfo[0]
            objectInfo = struct.unpack_from(object, rawData, offset + 1)
            offset += 1
            if (objectInfo[0] not in knownTags):
                raise ValueError(b"Could not parse object at index " + str(offset).encode("utf8") + b". Possible tags are " + currentTag + b" or " + objectInfo[0])



        print(b"Unpacked a " + objectInfo[0])
        children.append((offset, objectInfo))
        if objectInfo[0] in objectTypes:
            (newOffset, moreChildren) = objectTypes[objectInfo[0]](objectTypes, rawData, offset)
            offset = newOffset
        else:
            offset += objectInfo[1] + 8
        i += 1

    i = 0
    print("This group has " + str(header[-1]) + " children")
    while i < len(children):
        (newOffset, someString) = readGroupString(rawData, offset, i, len(children))
        offset = newOffset
        if someString == "":
            break
        finalChildren[someString.decode("utf8")] = children[i]
        i += 1
        print("Child: " + someString.decode("utf8"))

    for name, value in finalChildren.items():
        if value[1][0] == b"HERC" or value[1][0] == b"TANK" or value[1][0] == b"FLYR":
            with open(name + ".veh", "wb") as shapeFile:
                print("extracting " + name + ".veh")
                new_file_byte_array = bytearray(rawData[value[0]:value[0] + value[1][1] + 8])
                shapeFile.write(new_file_byte_array)
    print(len(finalChildren))
    return (offset, children)


objectTypes = {
    b"SIMG": readSimGroup,
    b"SVol": readSimVol
}

offset = 0

try:
    print(readSimGroup(objectTypes, rawData, offset))
except Exception as e:
    print(e, offset)

