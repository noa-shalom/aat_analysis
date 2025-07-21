from load_data import read_files_from_folder
from preprocess import df_preparation, remove_confusion_trials, look_for_zeros, extract_three_rt_measures, \
    remove_extreme_absolute_values, remove_outliers_address_error_trials, detect_outliers
from analyze import calc_grouped_acc_and_stats, calc_variables, create_results_table, create_dd_scores_table
from visualization import plot_removed_trials_summary, plot_rt_accuracy_summary, plot_dd_scores_by_emotion
from constants import cols_type_1, cols_type_2, initial_RT_mean_cols, initial_RT_accuracy_cols, \
    movement_duration_mean_cols, movement_duration_accuracy_cols, completion_time_mean_cols
import pandas as pd
import os
from stats_tests import analyze_rt_accuracy_tradeoff
from config_loader import load_config

# Note: Default is Adults, change to "kids.yaml" for the children version
config = load_config("config/kids.yaml")

# Read data
folder_path = config["raw_data_path"]
participants = read_files_from_folder(folder_path)
# Note: Default is using the full task, add a "half" argument (='first'/'second') to df_preparation below to change that
prep_participants = {participant_id: df_preparation(df, config) for participant_id, df in participants.items()}

# Pre-process
processed_participants = {}
processed_participants_no_err = {}
removed_trails = []
measures_per_condition = {}
measures_per_condition_no_err = {}

for participant_id, df in prep_participants.items():
    try:
        # Step 1: Remove confusion lines
        try:
            df_cleaned, confusion_lines_count = remove_confusion_trials(df, config)
        except Exception as e:
            raise RuntimeError(f"Error in 'remove_confusion_trials': {e}")

        # Step 2: Detect zeros
        try:
            z = look_for_zeros(df_cleaned)
        except Exception as e:
            raise RuntimeError(f"Error in 'look_for_zeros': {e}")

        # Step 3: Moving to three RTs only
        try:
            RT_measures = extract_three_rt_measures(df_cleaned)
        except Exception as e:
            raise RuntimeError(f"Error in 'extract_three_rt_measures': {e}")

        # Step 4: NaNs instead of zeros and extreme absolute values
        try:
            RT_measures_clean1 = remove_extreme_absolute_values(RT_measures, z, config)
        except Exception as e:
            raise RuntimeError(f"Error in 'remove_extreme_absolute_values': {e}")

        # Step 5: NaNs instead of outliers + Two versions creation
        try:
            RT_measures_clean2, nan_counts, RT_measures_clean2_no_err = remove_outliers_address_error_trials(
                RT_measures_clean1)
        except Exception as e:
            raise RuntimeError(f"Error in 'remove_outliers_address_error_trials': {e}")

        # Step 6: Removal flag + stats/acc calculation
        try:
            remove, m_per_cond = calc_grouped_acc_and_stats(RT_measures_clean2)
            remove2, m_per_cond2 = calc_grouped_acc_and_stats(RT_measures_clean2_no_err)
        except Exception as e:
            raise RuntimeError(f"Error in 'calc_grouped_acc_and_stats': {e}")

        # Save the processed DataFrames in the dictionaries
        processed_participants[participant_id] = RT_measures_clean2
        processed_participants_no_err[participant_id] = RT_measures_clean2_no_err
        measures_per_condition[participant_id] = m_per_cond
        measures_per_condition_no_err[participant_id] = m_per_cond2

        # Save removed lines count
        removed_trails.append({
            'ID': participant_id,
            'confusion_lines_count': confusion_lines_count,
            'zero_count': len(z),
            'initial_RT': nan_counts['initial_RT'],
            'movement_duration': nan_counts['movement_duration'],
            'completion_time': nan_counts['completion_time'],
            'low_accuracy_random_mistakes': remove,
            'more_than_50%_removal_flag': nan_counts[nan_counts > 96].any()
        })

    except Exception as e:
        print(f"Error processing participant {participant_id}: {e}")
        processed_participants[participant_id] = None  # Optionally, mark as None for inspection

# Visualize and save outliers summaries
removed_trails = pd.DataFrame(removed_trails)
removed_trails.set_index('ID', drop=True, inplace=True)
plot_removed_trials_summary(
    removed_trails=removed_trails,
    save_path=os.path.join(config["plots_dir"], "outliers_count.png")
)
outlier_dict = detect_outliers(removed_trails[['initial_RT', 'movement_duration', 'completion_time']])
all_outlier_indices = list(set([index for indices in outlier_dict.values() for index in indices]))
removed_trails['large_outliers_number'] = False
removed_trails.loc[all_outlier_indices, 'large_outliers_number'] = True
removed_trails.to_excel(os.path.join(config["results_dir"], "removed_trials.xlsx"),
                        sheet_name="removed_trials", index=True)

# Visualize key indices - finished preprocessing
plot_rt_accuracy_summary(
    measures_per_condition=measures_per_condition,
    measures_per_condition_no_err=measures_per_condition_no_err,
    save_path=os.path.join(config["plots_dir"], "RT_ACC_boxplots.png")
)

# double-difference D-scores calculation
dd_scores = calc_variables(processed_participants, measures_per_condition, config=config)
dd_scores_no_err = calc_variables(processed_participants_no_err, measures_per_condition_no_err, config=config)
dd_scores_df = create_dd_scores_table(dd_scores)
dd_scores_no_err_df = create_dd_scores_table(dd_scores_no_err)
dd_no_err = dd_scores_no_err_df[['ID', 'Emotion', 'initial_movement', 'first_full_movement']]
dd_full_data = dd_scores_df[['complete_movement']]
dd_final = pd.concat([dd_no_err, dd_full_data], axis=1)
dd_final.set_index('ID', inplace=True)
# Plot values
plot_dd_scores_by_emotion(
    dd_final=dd_final,
    save_path=os.path.join(config["plots_dir"], "complete_movement_scores.png")
)

# Create a results table
results_full_data = create_results_table(measures_per_condition, removed_trails)
results_no_err = create_results_table(measures_per_condition_no_err, removed_trails)
ordered_columns = results_full_data.columns
full_data_cols = results_full_data[cols_type_1]
no_err_data_cols = results_no_err[cols_type_2]
results_final = merged_df = pd.concat([full_data_cols, no_err_data_cols], axis=1)
results_final = results_final[ordered_columns]

# Save results and D-scores to separate sheets in the same Excel file
output_path = os.path.join(config["results_dir"], "AAT_results_final.xlsx")
with pd.ExcelWriter(output_path) as writer:
    results_final.to_excel(writer, sheet_name="RT + ACC", index=True)
    dd_final.to_excel(writer, sheet_name="double difference scores", index=True)
print("Excel file saved successfully!")

# Check Reaction Time - Accuracy Trade Off
samples = {'initial_RTs': results_final[initial_RT_mean_cols],
           'ACC_1': results_final[initial_RT_accuracy_cols],
           'movement_durations': results_final[movement_duration_mean_cols],
           'ACC_2': results_final[movement_duration_accuracy_cols],
           'completion_times': results_final[completion_time_mean_cols]}

analyze_rt_accuracy_tradeoff(samples, config=config)
print("Running is Done.")
