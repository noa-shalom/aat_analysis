import os
import pandas as pd


def read_files_from_folder(folder_path):
    """
    Reads .txt files of the AAT raw data into Pandas' DataFrames.

    Parameters:
    - folder_path (string): A path for a folder containing all the files.

    Returns:
    - participants (dict): Keys are participant's IDs; Values are DataFrames with the actual data.
    """
    # gets a list of all files in the folder that end with .txt
    files = sorted([os.path.join(folder_path, file) for file in os.listdir(folder_path) if file.endswith('.txt')])

    # reads each txt file into a DataFrame and store them in a dictionary with the filename as the key
    participants = {os.path.splitext(os.path.basename(file))[0]: pd.read_csv(file, delimiter='\t', header=None) for file in files}

    return participants
