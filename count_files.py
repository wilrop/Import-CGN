import sys
import os
from os import path
import gzip
import xml.etree.ElementTree as ET
from pydub import AudioSegment

DURATION = 4


# The definition that gets called with the target from main
def count_files(target):
    # Check to see if we get a correct path
    if not path.isdir(target):
        print("Could not locate the target")
    else:
        print("Found top level directory in: ", target)

    print("Locating the annotations")

    # Go to the transcription directory
    trans_path = path.join(target, "data/annot/xml/skp-ort")

    # The amount of files that will be created if we use DURATION amount of seconds at least per file
    num_files = 0

    # Check every file/directory at the given path
    for x in os.listdir(trans_path):
        new_trans_path = path.join(trans_path, x)
        # If we find a correct directory we need to enter
        if os.path.isdir(new_trans_path) and x.startswith("comp"):
            new_trans_path = path.join(trans_path, x)
            print("---------------------------------------------------------")
            print("Entering directory " + x)
            new_files = process_component(new_trans_path)
            num_files += new_files
            print(str(new_files) + " in " + new_trans_path)
            print("---------------------------------------------------------")

    # Do times two because we do the same splits for every audio file
    num_files = num_files * 2
    print("The number of files created with at least " + str(DURATION) + " seconds is: " + str(num_files))


# This definition will process one component at a time at the given paths.
def process_component(trans_path):
    # Loop over every directory (= language)
    files = 0
    for directory in os.listdir(trans_path):
        print("Processing files for language: " + directory)
        trans_dir = path.join(trans_path, directory)
        for file in os.listdir(trans_dir):
            if file.startswith("fn") or file.startswith("fv"):
                files += count_file(trans_dir, file)
        print("Finished processing language: " + directory)

    return files


def count_file(trans_dir, filename):
    # The current filename ends with .wav but we need it to be .skp
    name = filename.split(".")[0]
    filename = name + ".skp"
    trans_path = path.join(trans_dir, filename)

    # If the file does not exist, it means that it has not been extracted
    if not path.exists(trans_path):
        zipped_file = filename + ".gz"
        trans_path = path.join(trans_dir, zipped_file)
        # We open the zipped file and parse the tree from it
        with gzip.open(trans_path) as trans_file:
            tree = ET.parse(trans_file)

    # Otherwise the file is extracted and we can just parse instantly
    else:
        trans_path = path.join(trans_dir, filename)
        trans_file = open(trans_path, "r")
        tree = ET.parse(trans_file)

    root = tree.getroot()

    begin = 0
    end = 0
    files = 0

    # This for loop will iterate over all the "tau" segments (more or less equal to a sentence each)
    for tau in root.iter("tau"):
        seg_begin = float(tau.get("tb"))  # The begin of the segment
        seg_end = float(tau.get("te"))

        # If we start at a new segment we have to reset the beginning
        if end == 0:
            begin = seg_begin

        end = seg_end
        duration = end - begin
        if duration >= DURATION:
            end = 0
            files += 1

    return files


if __name__ == "__main__":
    print("Starting the counting of the data")

    count_files(sys.argv[1])

    print("Completed successfully")