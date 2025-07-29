import pandas as pd
import numpy as np


def df_preparation(df, config, half=None):
    """
    Organizes the DataFrames for following analysis.
    - splits the originally one-column df into a multiple-columns df
    - deletes instructions, practice and summary rows
    - converts reaction time values from strings to numeric
    - edits the trial-type column, keeping only relevant information
    - notifies in cases of inappropriate ID pattern

    Parameters:
    - df (DataFrame): A raw data df, of one participant.

    Returns:
    - df (DataFrame): A clean df.
    """
    # splitting it into columns
    df = df[0].str.split(' ', expand=True)
    SDAN = df.iloc[0, 0]

    # deleting instructions, practice and summary rows
    rows_to_delete = (
            df[1].str.contains('INSTRUCTIONS|PRACTICE', na=False) |
            ~df[0].str.contains(config["id_prefix"], na=False)
    )

    df = df[~rows_to_delete].reset_index(drop=True)

    # converting RTs to numeric
    df.iloc[:, 3::2] = df.iloc[:, 3::2].apply(pd.to_numeric, errors='coerce')

    # shortning the strings column
    df.iloc[:, 1] = df.iloc[:, 1].str[-22:]  # current trial only
    df.iloc[:, 1] = df.iloc[:, 1].str[0:4] + '_' + df.iloc[:, 1].str[15:18]

    # Optional: Take only task's first half
    if half is not None:
        if half == 'first':
            df = df.iloc[0:round(len(df) / 2), :]
        if half == 'second':
            df = df.iloc[round(len(df) / 2)+1:, :]

    # notifying exceptional SDAN
    if len(SDAN) != config["id_length"] or SDAN[:2] != config["id_prefix"]:
        print(f"Check {SDAN} SDAN")

    return df


def remove_confusion_trials(df, config):
    """
    Removes trials in which the participant changed the joystick direction more than three times (four times for kids).
    NOTE: this is the only processing step that removes full rows.

    Parameters:
    - df: one participant's data.

    Returns:
    - df: the same df without the confusion trials.
    - confusion_lines_count (int): number of deleted rows.
    """
    # Identify rows with three or more 'MIDDL' occurrences
    middl_idx = df == "MIDDL"
    mid_count_per_row = middl_idx.sum(axis=1)
    confusion_lines = mid_count_per_row[mid_count_per_row >= config["max_middl_count"]].index
    confusion_lines_count = len(confusion_lines)

    # Drop rows identified as "confusion lines" and reset the index
    df = df.drop(index=confusion_lines).reset_index(drop=True)

    return df, confusion_lines_count


def look_for_zeros(df):
    """
    Search for rows with zeros in the participant's data.
    For these trials, only the completion RT (the third measure) will be taken for analysis.

    parameters:
    - df: one participant's data.

    Returns:
    - zero_row_indices (list): rows in which zeros were detected.
    """
    # Identify rows with any zero values
    numeric_columns = df.iloc[:, 3::2]
    zero_row_indices = numeric_columns.index[(numeric_columns == 0).any(axis=1)].tolist()

    return zero_row_indices


def extract_three_rt_measures(df):
    """
    Gets three RT measurememts for each trial: initiation time, movement duration, and completion time.

    Parameters:
    - df: one participant's data.

    Returns:
    - RT_measures (df): reduced participant's df, including cols only for trial_type and the three relevant RT measures.
    """
    # Trial-type column
    trial_type = df[1]

    # PULL1/PUSH1 columns
    initial_movement = df[2]
    initial_RT = df[3].to_numpy()

    # First full movement columns
    pull5_or_push5_positions = (df == "PULL5") | (df == "PUSH5")  # Boolean DataFrame
    leftmost_positions = pull5_or_push5_positions.idxmax(axis=1)  # Get first occurrence per row
    first_full_movement = []
    movement_duration = []
    for idx, col in leftmost_positions.items():
        if col in df.columns and col + 1 in df.columns:  # Ensure we don't go out of bounds
            first_full_movement.append(df.iat[idx, col])  # Take the movement type
            movement_duration.append(df.iat[idx, col + 1])  # Take the RT value in the next column
        else:  # Handle edge cases safely
            first_full_movement.append(None)
            movement_duration.append(None)
    movement_duration = pd.to_numeric(movement_duration, errors='coerce')

    # RT for the picture to disappear
    break_positions = (df == "BREAK")  # Boolean DataFrame
    break_locations = break_positions.idxmax(axis=1)  # Get first occurrence per row
    completion_time = []
    for idx, col in break_locations.items():
        if pd.notna(col) and col in df.columns and col - 1 in df.columns:  # Ensure within range
            completion_time.append(df.iat[idx, col - 1])  # Take the RT value in the previous column
        else:
            completion_time.append(None)  # Handle edge cases safely
    completion_time = pd.to_numeric(completion_time, errors='coerce')

    # Create RT measures dataframe
    RT_measures = pd.DataFrame({
        'trial_type': trial_type,
        'initial_movement': initial_movement,
        'initial_RT': initial_RT,
        'first_full_movement': first_full_movement,
        'movement_duration': movement_duration,
        'completion_time': completion_time
    })

    return RT_measures


def remove_extreme_absolute_values(RT_measures, zero_row_indices, config):
    """
    Replace the following values with NaNs:
    - 'initial_RT' that is not between 150 and 2000 (150 and 3000 for kids).
    - 'completion_time' that is not between 300 and 3000 (300 and 4500 for kids).
    - 'initial_RT' and 'movement_duration' in rows where zeros were detected.

    Parameters:
    - RT_measures (df): participant's 3 RT measurements.
    - zero_row_indices (list): rows in which zeros were detected.

    Returns:
    - RT_measures_clean1 (df): an updated df, with NaNs
    """
    # Crete a df copy
    RT_measures_clean1 = RT_measures.copy()

    # Identify extreme 'completion_time' values
    extreme_completion_time = ((RT_measures['completion_time'] < config["lower_completion_threshold"]) |
                               (RT_measures['completion_time'] > config["upper_completion_threshold"]))
    RT_measures_clean1.loc[extreme_completion_time, 'completion_time'] = None

    # Identify extreme 'initial_RT' values
    extreme_initial_RT = ((RT_measures['initial_RT'] < config["lower_initial_threshold"]) |
                          (RT_measures['initial_RT'] > config["upper_initial_threshold"]))
    RT_measures_clean1.loc[extreme_initial_RT, 'initial_RT'] = None

    # Address zero lines
    RT_measures_clean1.loc[zero_row_indices, ['initial_RT', 'movement_duration']] = None

    return RT_measures_clean1


def remove_outliers_address_error_trials(RT_measures_clean1):
    """
    Removes outliers based on stats calculated without error trials.
    Creates two versions for each participant: with and without error trials.

    Parameters:
    - RT_measures_clean1 (df): DataFrame containing reaction time measures (after partial cleaning).

    Returns:
    - RT_measures_clean2: an updated df with outliers removed.
    - RTs_no_errors: an updated df with outliers removed and without error trials.
    """
    # Detect trials the participant made a mistake
    is_initial_acc = [
        RT_measures_clean1.loc[i, 'trial_type'][0:4] == RT_measures_clean1.loc[i, 'initial_movement'][0:-1] for i in
        range(len(RT_measures_clean1))]
    error_trials_initial = [i for i, acc in enumerate(is_initial_acc) if not acc]
    is_full_acc = [
        RT_measures_clean1.loc[i, 'trial_type'][0:4] == RT_measures_clean1.loc[i, 'first_full_movement'][0:-1] for i in
        range(len(RT_measures_clean1))]
    error_trials_full = [i for i, acc in enumerate(is_full_acc) if not acc]
    error_trials = list(pd.Series(error_trials_initial + error_trials_full).unique())

    # Exclude error lines for stats calculation
    RT_measures_without_errors = RT_measures_clean1.drop(index=error_trials, errors='ignore')

    # Select only the numeric columns for stats calculation
    numeric_columns = ['initial_RT', 'movement_duration', 'completion_time']
    RT_measures_numeric = RT_measures_without_errors[numeric_columns]

    # Calculate (three) mean, std, and thresholds
    mean_row = RT_measures_numeric.mean()
    std_row = RT_measures_numeric.std()
    upper_threshold = mean_row + 2.5 * std_row
    lower_threshold = mean_row - 2.5 * std_row

    # Detect outliers in the original DataFrame based on thresholds and remove them
    RT_measures_clean2 = RT_measures_clean1.copy()
    is_outlier = RT_measures_clean2[numeric_columns].apply(
        lambda col: (col < lower_threshold[col.name]) | (col > upper_threshold[col.name]))
    RT_measures_clean2[numeric_columns] = RT_measures_clean2[numeric_columns].mask(is_outlier)

    # Count NaNs per RT measure
    nan_counts = RT_measures_clean2[numeric_columns].isna().sum()

    # Make a copy without error trials
    RT_measures_clean2_no_errors = RT_measures_clean2.drop(index=error_trials, errors='ignore')
    return RT_measures_clean2, nan_counts, RT_measures_clean2_no_errors


def detect_outliers(df):
    outliers = {}
    for col in df.columns:
        Q1 = np.percentile(df[col], 25)
        Q3 = np.percentile(df[col], 75)
        IQR = Q3 - Q1
        upper_bound = Q3 + 1.5 * IQR  # Outliers above this value

        # Get indexes of outliers
        outlier_indices = df[df[col] > upper_bound].index.tolist()

        if outlier_indices:
            outliers[col] = outlier_indices  # Store indices of outliers

        print(f"{col}: Upper bound = {upper_bound:.2f}, Outliers: {outlier_indices}")

    return outliers
