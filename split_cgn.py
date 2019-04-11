import sys
import os
from os import path
import gzip
import xml.etree.ElementTree as ET
from pydub import AudioSegment


# The definition that gets called with the target from main
def split_files(target):
    # Check to see if we get a correct path
    if not path.isdir(target):
        print("Could not locate the target")
    else:
        print("Found top level directory in: ", target)

    print("Locating the sound files and corresponding annotations")

    # Go to the audio and transcription directories
    audio_path = path.join(target, "data/audio/wav")
    trans_path = path.join(target, "data/annot/xml/skp-ort")

    # Check every file/directory at the given path
    for x in os.listdir(audio_path):
        new_audio_path = path.join(audio_path, x)
        # If we find a correct directory we need to enter
        if os.path.isdir(new_audio_path) and x.startswith("comp"):
            new_trans_path = path.join(trans_path, x)
            print("---------------------------------------------------------")
            print("Entering directory " + x)
            process_component(new_audio_path, new_trans_path)
            print("---------------------------------------------------------")


# This definition will process one component at a time at the given paths.
def process_component(audio_path, trans_path):
    # Loop over every directory (= language)
    for directory in os.listdir(audio_path):
        print("Processing files for language: " + directory)
        audio_dir = path.join(audio_path, directory)
        trans_dir = path.join(trans_path, directory)
        for file in os.listdir(audio_dir):
            split_file(audio_dir, trans_dir, file)
        print("Finished processing language: " + directory)


def split_file(audio_dir, trans_dir, filename):
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
    i = 0  # A counter

    # This for loop will iterate over all the "tau" segments (more or less equal to a sentence each)
    for tau in root.iter("tau"):
        begin = float(tau.get("tb"))  # The begin of the segment
        end = float(tau.get("te"))

        # Construct a new file with the given counter
        new_file = name + "(" + str(i) + ")" + ".skp"
        new_trans_path = path.join(trans_dir, new_file)
        f = open(new_trans_path, "wb+")

        # Write the file
        xml_string = ET.tostring(tau)
        f.write(xml_string)

        # Split the audio file at the given timestamps
        split_audio(audio_dir, name, i, begin, end)

        i += 1  # update the counter

    # Remove the original files to save space
    if os.path.exists(trans_path):
        os.remove(trans_path)
    audio_name = name + ".wav"
    audio_path = path.join(audio_dir, audio_name)
    if os.path.exists(audio_path):
        os.remove(audio_path)


# This definition will split an audio file and save it under a new name
def split_audio(audio_dir, name, i, begin, end):
    # Get the original file and make it into an AudioSegment
    original_name = name + ".wav"
    audio_path = path.join(audio_dir, original_name)
    audio_file = AudioSegment.from_wav(audio_path)

    # Construct the new fragment
    begin = begin * 1000  # The module uses milliseconds
    end = end * 1000
    new_fragment = audio_file[begin:end]

    # Save the new file
    new_name = name + "(" + str(i) + ")" + ".wav"
    new_audio_path = path.join(audio_dir, new_name)
    new_fragment.export(new_audio_path, format="wav")


if __name__ == "__main__":
    print("Starting the splitting of the data")

    split_files(sys.argv[1])

    print("Completed successfully")
