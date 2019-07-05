#!/usr/bin/env python

import os
from os import path
import argparse         # This module is used to pass optional flags to the importer
import soundfile as sf  # This module is used to calculate the length of the sound files
import pandas as pd     # Pandas is used to construct the CSV file
import xml.etree.ElementTree as ET      # This is used to parse the XML file with the transcriptions
import gzip          # This is used to extract the transcriptions if they are still zipped

# Global variable specifying the maximum and minimum accepted lengths of a speech file
MAX_SECS = 10
MIN_SECS = 3

# The filenames for the splits
FILENAME_TRAIN = "train_data_strip.csv"
FILENAME_DEV = "dev_data_strip.csv"
FILENAME_TEST = "test_data_strip.csv"

# The percentage by which we split the training and testing sets
TRAIN_SPLIT = 0.8

# Forbidden characters that we do not want to have in our transcription
CHARACTERS = ["0", "1", "2", "3", "4", "5", "6", "7", "8", "9"]
WORDS = ["ggg", "Xxx", "xxx"]


# This function will preprocess the data given a target (the top level directory of CGN)
def preprocess_data(args):

    target = args.target

    # Check to see if we get a correct path
    if not path.isdir(target):
        print("Could not locate the target")
    else:
        print("Found top level directory in: ", target)

    print("Locating the sound files and corresponding annotations")

    # Go to the audio and transcription directories
    audio_path = path.join(target, "data/audio/wav")
    trans_path = path.join(target, "data/annot/xml/skp-ort")

    # The dataframe holding all the data
    data = pd.DataFrame()

    # Check if the user chose a specific component
    if args.components:
        print("Components: " + str(args.components))
        for comp in args.components:
            new_audio_path = path.join(audio_path, "comp-" + comp)
            new_trans_path = path.join(trans_path, "comp-" + comp)
            if not path.isdir(audio_path):
                print("The given component: " + comp + " could not be found")
            else:
                print("---------------------------------------------------------")
                print("Entering directory " + comp)
                new_data = process_component(new_audio_path, new_trans_path)
                data = data.append(new_data)
                print("---------------------------------------------------------")
    else:
        print("Utilizing all available components")
        # Check everything at the given path. The subdirectories are the same for audio and trans
        for x in os.listdir(audio_path):
            new_audio_path = path.join(audio_path, x)
            # If we find a correct directory we need to enter
            if os.path.isdir(new_audio_path) and x.startswith("comp"):
                new_trans_path = path.join(trans_path, x)
                print("---------------------------------------------------------")
                print("Entering directory " + x)
                new_data = process_component(new_audio_path, new_trans_path)
                data = data.append(new_data)
                print("---------------------------------------------------------")

    # Generate the final splits
    generate_splits(data)


# This function takes care of one component of the data
def process_component(audio_path, trans_path):
    lang = args.language

    data = pd.DataFrame()
    # If flemish is selected we will enter this
    # If no language was chose we want both so we also enter this
    if not lang or lang == "vl":
        print("Processing the Flemish language files")
        new_audio_path = path.join(audio_path, "vl")
        new_trans_path = path.join(trans_path, "vl")
        # This check is just to make sure the directory exists
        if os.path.isdir(new_audio_path):
            new_data = process_language(new_audio_path, new_trans_path)
            data = data.append(new_data)
        else:
            print("Directory does not exist")

    # Same here for the dutch language
    if not lang or lang == "nl":
        print("Processing the Dutch language files")
        new_audio_path = path.join(audio_path, "nl")
        new_trans_path = path.join(trans_path, "nl")
        if os.path.isdir(new_audio_path):
            new_data = process_language(new_audio_path, new_trans_path)
            data = data.append(new_data)
        else:
            print("Directory does not exist")

    if lang and lang != "nl" and lang != "vl":
        print("The provided language was invalid")

    return data


# This function processes one language each time it gets called
def process_language(audio_path, trans_path):
    files = sorted(os.listdir(audio_path))  # Needs to be sorted so that we can use the "previous" later.
    accepted = 0
    accepted_wavs = []
    accepted_wav_sizes = []
    accepted_wav_transcripts = []
    rejected = 0

    previous_end = 0
    possible_file = None
    possible_filesize = 0
    possible_transcript = ""

    def maybe_add(possible_file, possible_filesize, possible_transcript):
        if possible_transcript and possible_transcript != "":
            print("File: " + possible_file + " and Transcript: " + str(possible_transcript))
            # Import the previous file.
            nonlocal accepted
            accepted += 1
            accepted_wavs.append(possible_file)
            accepted_wav_sizes.append(possible_filesize)
            accepted_wav_transcripts.append(possible_transcript)
        else:
            nonlocal rejected
            rejected += 1

    # Check all speech files for validity
    for idx, file in enumerate(files):
        print(possible_file)
        final_path = path.join(audio_path, file)

        # Calculate the length of the speech file
        speech = sf.SoundFile(final_path)
        samples = len(speech)
        sample_rate = speech.samplerate
        seconds = samples/sample_rate

        if "(" not in file:  # The original file is still there but we only want to account for files that are split
            continue
        elif seconds > MAX_SECS or seconds < MIN_SECS:
            print("Too long Rejection: " + file)
            rejected += 1
        else:
            # The function returns the timestamps and the transcription for the .wav file
            begin, end, transcript = get_transcription(file, trans_path)
            if possible_file is None:
                pass
            elif file.endswith("(000).skp"): # When we start processing a new "big" file.
                maybe_add(possible_file, possible_filesize, possible_transcript)
            elif previous_end <= begin < end:
                maybe_add(possible_file, possible_filesize, possible_transcript)
                if idx == len(files) - 1:
                    # Also import the current file.
                    maybe_add(file, os.path.getsize(final_path), transcript)
            else:
                print("Time Rejection: " + possible_file)
                transcript = ""  # We do this so the file will also be rejected later on
                rejected += 1

            # Set the current file as a possible candidate for importing.
            possible_file = final_path
            possible_filesize = os.path.getsize(final_path)
            possible_transcript = transcript
            previous_end = end

    processed_data = {
        'wav_filename': accepted_wavs,
        'wav_filesize': accepted_wav_sizes,
        'transcript': accepted_wav_transcripts
    }

    # A data frame of all the processed data
    df = pd.DataFrame(processed_data, columns=['wav_filename', 'wav_filesize', 'transcript'])

    print("Number of rejected files: " + str(rejected))
    print("Number of accepted files: " + str(accepted))

    return df


# This function generates the transcription for the given audio file
def get_transcription(audio_file, directory_path):
    # The current filename ends with .wav but we need it to be .skp
    filename = audio_file.split(".")[0]
    filename += ".skp"
    trans_path = path.join(directory_path, filename)

    # If the file does not exist, it means that it has not been extracted
    if not path.exists(trans_path):
        zipped_file = filename + ".gz"
        zipped_path = path.join(directory_path, zipped_file)
        # We open the zipped file and parse the tree from it
        with gzip.open(zipped_path) as trans_file:
            tree = ET.parse(trans_file)

    # Otherwise the file is extracted and we can just parse instantly
    else:
        trans_file = open(trans_path, "r")
        tree = ET.parse(trans_file)

    root = tree.getroot()
    tau = root.find("tau")

    # Get the beginning and ending already. Initialize the transcription.
    begin = tau.get("tb")
    end = tau.get("te")
    transcription = ""

    # All words are inside tags <tw .....> so we iterate over them
    for tw in root.iter("tw"):
        word = tw.get("w")
        if word in WORDS:
            return begin, end, False
        for letter in word:
            if letter in CHARACTERS:
                return begin, end, False

        transcription += word + " "

    # Strip the last character which is an unnecessary space and make it all lowercase.
    transcription = transcription[:-1].lower()

    # Return the complete transcription
    return begin, end, transcription


def check_previous(previous_end, begin, end):
    return previous_end <= begin < end


def generate_splits(data):
    print("Generating splits for the data")

    # Randomize the order of the data
    data = data.sample(frac=1)

    # We split into 80-20 training and testing (using the global variable TRAIN_SPLIT)
    # Afterwards we split the 80% training data into 80-20 training validation
    train_beg = 0
    train_end = int(TRAIN_SPLIT * len(data))
    dev_beg = int(TRAIN_SPLIT * train_end)
    dev_end = train_end
    train_end = dev_beg
    test_beg = dev_end
    test_end = len(data)

    # Make the splits
    train_data = data[train_beg:train_end]
    dev_data = data[dev_beg:dev_end]
    test_data = data[test_beg:test_end]

    # We write the splits
    print("Writing training split")
    with open(FILENAME_TRAIN, 'a') as f:
        # We only want to write the header the first time, hence the quick check "header = ..."
        train_data.to_csv(f, sep=',', mode='a', header=True, index=False, encoding="ascii")

    print("Writing validation split")
    with open(FILENAME_DEV, 'a') as f:
        # We only want to write the header the first time, hence the quick check "header = ..."
        dev_data.to_csv(f, sep=',', mode='a', header=True, index=False, encoding="ascii")

    print("Writing test split")
    with open(FILENAME_TEST, 'a') as f:
        # We only want to write the header the first time, hence the quick check "header = ..."
        test_data.to_csv(f, sep=',', mode='a', header=True, index=False, encoding="ascii")


if __name__ == "__main__":
    print("Starting the preprocessing of the data")

    # Starting the parser for the command line arguments
    parser = argparse.ArgumentParser()
    parser.add_argument("target", help="the top level target directory")
    parser.add_argument("--components", nargs='+', help="restrict the used data to a specified component")
    parser.add_argument("--language", help="choose a single language for the model")
    args = parser.parse_args()

    # Getting rid of the previous CSV files if they exist
    if os.path.exists(FILENAME_TRAIN):
        os.remove(FILENAME_TRAIN)
    if os.path.exists(FILENAME_DEV):
        os.remove(FILENAME_DEV)
    if os.path.exists(FILENAME_TEST):
        os.remove(FILENAME_TEST)

    preprocess_data(args)

    print("Completed successfully")
