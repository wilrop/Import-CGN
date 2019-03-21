#!/usr/bin/env python

import os
from os import path
import argparse         # This module is used to pass optional flags to the importer
import soundfile as sf  # This module is used to calculate the length of the sound files
import pandas as pd     # Pandas is used to construct the CSV file

# Global variable specifying the maximum accepted length of a speech file
MAX_SECS = 10


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
    trans_path = path.join(target, "data/annot/text/ort")

    # Check if the user chose a specific component
    if args.component:
        audio_path = path.join(audio_path, "comp-" + args.component)
        trans_path = path.join(trans_path, "comp-" + args.component)
        if not path.isdir(audio_path):
            print("The given component could not be found")
        else:
            print("---------------------------------------------------------")
            print("Only utilizing the specified component " + args.component)
            process_component(audio_path, trans_path)
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
                process_component(new_audio_path, new_trans_path)
                print("---------------------------------------------------------")


def process_component(audio_path, trans_path):
    lang = args.language
    # If flemish is selected we will enter this
    # If no language was chose we want both so we also enter this
    if not lang or lang == "vl":
        print("Processing the Flemish language files")
        new_audio_path = path.join(audio_path, "vl")
        new_trans_path = path.join(trans_path, "vl")
        # This check is just to make sure the directory exists
        if os.path.isdir(new_audio_path):
            process_language(new_audio_path, new_trans_path)
        else:
            print("Directory does not exist")

    # Same here for the dutch language
    if not lang or lang == "nl":
        print("Processing the Dutch language files")
        new_audio_path = path.join(audio_path, "nl")
        new_trans_path = path.join(trans_path, "nl")
        if os.path.isdir(new_audio_path):
            process_language(new_audio_path, new_trans_path)
        else:
            print("Directory does not exist")

    if lang and lang != "nl" and lang != "vl":
        print("The provided language was invalid")


def process_language(audio_path, trans_path):
    files = os.listdir(audio_path)
    accepted = 0
    accepted_list = []
    rejected = 0

    # Check all speech files for validity
    for file in files:
        final_path = path.join(audio_path, file)

        # Calculate the length of the speech file
        speech = sf.SoundFile(final_path)
        samples = len(speech)
        sample_rate = speech.samplerate
        seconds = samples/sample_rate

        if seconds > MAX_SECS:
            rejected += 1
        else:
            accepted +=1
            accepted_list.append(file)

    print("Number of rejected files: " + str(rejected))
    print("Number of accepted files: " + str(accepted))
    print("Accepted files:")
    print(accepted_list)


if __name__ == "__main__":
    print("Starting the preprocessing of the data")

    # Starting the parser for the command line arguments
    parser = argparse.ArgumentParser()
    parser.add_argument("target", help="the top level target directory")
    parser.add_argument("--component", help="restrict the used data to a specified component")
    parser.add_argument("--language", help="choose a single language for the model")
    args = parser.parse_args()

    preprocess_data(args)

    print("Completed successfully")
