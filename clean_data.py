import argparse
import pandas as pd
from os import path


def clean(args):
    file = args.file
    df = pd.read_csv(file)
    print("There are " + str(len(df)) + " in the original file")

    # Iterate over all rows in the dataframe
    for index, row in df.iterrows():
        row['transcript'].replace("-", " ")  # Replace - by a space
        if row['transcript'].find('&') == -1:  # Drop all rows containing a &
            df.drop(index, inplace=True)

    print("There are " + str(len(df)) + " in the cleaned file")

    # We write the cleaned file
    print("Writing cleaned file")
    new_file = path.dirname(file) + "/cleaned_" + path.basename(file)
    with open(new_file, 'a') as f:
        # We only want to write the header the first time, hence the quick check "header = ..."
        df.to_csv(f, sep=',', index=False, encoding="ascii")


# The main function
if __name__ == "__main__":
    print("Starting the cleaning of the data")

    # Starting the parser for the command line arguments
    parser = argparse.ArgumentParser()
    parser.add_argument("file", help="the file that will be cleaned")
    args = parser.parse_args()

    clean(args)

    print("Completed successfully")