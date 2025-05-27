import pandas as pd
import numpy as np
from scipy.stats import chisquare


def calc_grouped_acc_and_stats(RT_measures_clean2):
    """
    Per condition, calculates accuracy precentages for initial movement and first full movement (since participant's reaction can be correct or incorrect),
    as well as statistics (mean and std).
    Records participants who preformed poorly in the whole task (below 50% accuracy & random errors distribution across conditions).
    Records error trials' indices.

    Parameters:
    - RT_measures_clean2: DataFrame containing reaction time measures (after full cleaning).

    Returns:
    - remove (bool): True = flag for poor preformance (low acc)
    - m_per_cond (df): mean, std and acc X the 8 conditions
    """

    # Initial movement accuracy
    df = RT_measures_clean2.copy()
    is_initial_acc = [df.loc[i, 'trial_type'][0:4] == df.loc[i, 'initial_movement'][0:-1] for i in df.index]
    error_trials_initial = [i for i, acc in enumerate(is_initial_acc) if not acc]
    initial_acc = np.mean(is_initial_acc)
    remove = False
    if initial_acc < 0.5:
        trial_type_errors = RT_measures_clean2.iloc[error_trials_initial, 'trial_type']
        mistakes_per_condition = trial_type_errors.value_counts()
        all_conditions = set(RT_measures_clean2['trial_type'].dropna())
        mistakes_per_condition = mistakes_per_condition.reindex(all_conditions, fill_value=0)
        expected = [sum(mistakes_per_condition) / 8] * 8
        chi2_stat, p_value = chisquare(f_obs=mistakes_per_condition, f_exp=expected)
        if p_value > 0.05:
            remove = True

    # First full movement accuracy
    is_full_acc = [df.loc[i, 'trial_type'][0:4] == df.loc[i, 'first_full_movement'][0:-1] for i in df.index]
    error_trials_full = [i for i, acc in enumerate(is_full_acc) if not acc]
    first_full_movement_acc = np.mean(is_full_acc)

    # Mean, STD & Accuracy per condition
    numeric_cols = ["initial_RT", "movement_duration", "completion_time"]
    grouped_mean = df.groupby("trial_type")[numeric_cols].mean().add_suffix("_mean")
    grouped_std = df.groupby("trial_type")[numeric_cols].std().add_suffix("_std")
    acc_df = pd.DataFrame({
        'trial_type': df['trial_type'],
        'initial_RT_accuracy': is_initial_acc,
        'movement_duration_accuracy': is_full_acc
    })
    grouped_acc = acc_df.groupby("trial_type")[["initial_RT_accuracy", "movement_duration_accuracy"]].mean()
    measures_per_cond = pd.concat([grouped_mean, grouped_std, grouped_acc], axis=1)

    # Add the overall measures
    means = df[numeric_cols].mean().add_suffix("_mean")
    stds = df[numeric_cols].std().add_suffix("_std")
    overall_accuracy = pd.Series(
        {'initial_RT_accuracy': initial_acc, 'movement_duration_accuracy': first_full_movement_acc}).T
    overall_row = pd.DataFrame([pd.concat([means, stds, overall_accuracy])])
    overall_row.index = ["overall"]  # Explicitly set the index
    measures_per_cond = pd.concat([measures_per_cond, overall_row], axis=0)

    return remove, measures_per_cond


def create_results_table(participants_dict, removed_trails):
    """
    Creates a single results dataframe from all individual participants' dataframes.

    Parameters:
    - participants_dict (dict): keys are IDs, values are measurements DataFrames.

    Returns:
    - results (pd.DataFrame): A DataFrame where each row corresponds to a participant.
    """

    results = pd.DataFrame()

    for id, measures in participants_dict.items():
        # Flatten DataFrame
        flat_measures = measures.unstack().to_frame().T

        # Check if columns are multi-index and flatten them accordingly
        flat_measures.columns = ['{}_{}'.format(col, idx) for idx, col in flat_measures.columns]

        # Set participant ID as index
        flat_measures.index = [id]

        # Add to the results df
        results = pd.concat([results, flat_measures])

    # Reset index for a clean structure
    results.index.name = "ID"
    results.reset_index(inplace=True)

    # Get info from removed_trails
    info = removed_trails[["low_accuracy_random_mistakes", "more_than_50%_removal_flag"]]

    # Re-order columns
    ordered_columns = ["ID"]

    conditions = ['overall', 'PULL_ANG', 'PULL_HAP', 'PULL_NEU', 'PULL_SAD', 'PUSH_ANG', 'PUSH_HAP', 'PUSH_NEU',
                  'PUSH_SAD']
    rts = ["initial_RT", "movement_duration", "completion_time"]

    for cond in conditions:
        for rt in rts:
            if rt == "completion_time":
                stats_subset = ["mean", "std"]  # No "accuracy" for completion_time
            else:
                stats_subset = ["mean", "std", "accuracy"]  # Keep accuracy for initial_RT & movement_duration

            for stat in stats_subset:
                col_name = f"{cond}_{rt}_{stat}"
                if col_name in results.columns:
                    ordered_columns.append(col_name)
                else:
                    print(f"Missing column: {col_name}")

    results = results[ordered_columns]
    results.set_index("ID", inplace=True)
    results_final = pd.merge(results, info, left_index=True, right_index=True)
    return results_final


def calc_variables(processed_participants, measures_per_condition, config):
    """
    Computes normalized double-difference scores for each participant.

    Parameters:
    - processed_participants (dict): Dictionary where keys are participant IDs, and values are DataFrames containing their data.
    - measures_per_condition (dict): Dictionary where keys are participant IDs, and values contain summary statistics.

    Returns:
    - norm_d_scores (dict): Dictionary with normalized double-difference scores for each participant.
    """

    # Extract experimental conditions
    experimental_conditions = set(processed_participants[config["id_for_example"]]['trial_type'].dropna())

    # Aggregate Reaction Times (RTs)
    aggregated_rt = {}
    for id, df in processed_participants.items():
        temp_dict = {}
        for c in experimental_conditions:
            temp_dict[c] = df.loc[df['trial_type'] == c, ['initial_RT', 'movement_duration', 'completion_time']].mean(
                axis=0)
        aggregated_rt[id] = temp_dict

    # Compute Double-Difference Scores
    double_diff_scores = {}
    for id, agg_rt in aggregated_rt.items():
        diff = {}
        for stim in ["HAP", "SAD", "ANG", "NEU"]:
            diff[stim] = agg_rt[f'PUSH_{stim}'] - agg_rt[f'PULL_{stim}']
        double_diff = {}
        for stim in ["HAP", "SAD", "ANG"]:
            double_diff[stim] = diff[stim] - diff['NEU']
        double_diff_scores[id] = double_diff

    # Normalize with D-Score
    # norm_d_scores = {}
    # for id, dd in double_diff_scores.items():
    #    std = measures_per_condition[id].loc['overall', ['initial_RT_std', 'movement_duration_std', 'completion_time_std']].dropna()
    #    temp_dict = {stim: np.array(dd[stim]) / std.values for stim in ["HAP", "SAD", "ANG"]}
    #    norm_d_scores[id] = temp_dict

    return double_diff_scores


def create_dd_scores_table(dd_scores):
    data = []
    for id, scores in dd_scores.items():
        for emotion in ["HAP", "SAD", "ANG"]:
            data.append({
                "ID": id,
                "Emotion": emotion,
                "initial_movement": scores[emotion][0],
                "first_full_movement": scores[emotion][1],
                "complete_movement": scores[emotion][2]
            })

    data_df = pd.DataFrame(data)

    return data_df
