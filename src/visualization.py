import matplotlib.pyplot as plt
import pandas as pd


def annotate_outliers(ax, data, label_x):
    # Compute IQR
    Q1 = data.quantile(0.25)
    Q3 = data.quantile(0.75)
    IQR = Q3 - Q1
    lower_bound = Q1 - 1.5 * IQR
    upper_bound = Q3 + 1.5 * IQR

    # Get outliers
    outliers = data[(data < lower_bound) | (data > upper_bound)]

    # Annotate each outlier
    for idx, y_val in outliers.items():
        ax.annotate(str(idx), xy=(label_x, y_val), xytext=(label_x + 0.05, y_val),
                    ha='left', va='center', fontsize=8, color='red')


def plot_removed_trials_summary(removed_trails, save_path):
    """
    Plots a 3-panel boxplot showing the number of removed trials for
    initial RT, movement duration, and completion time. Annotates outliers.

    Parameters:
    - removed_trails (pd.DataFrame): DataFrame with 'initial_RT', 'movement_duration', and 'completion_time' columns.
    - save_path (str): Full path to save the output plot (including .png).
    """
    fig, axes = plt.subplots(1, 3, figsize=(15, 5))

    metrics = ['initial_RT', 'movement_duration', 'completion_time']
    titles = ['removed initial rt', 'removed first full movements', 'removed completion times']

    for i, metric in enumerate(metrics):
        axes[i].boxplot(removed_trails[metric], showmeans=True, notch=True)
        axes[i].set_title(titles[i])
        axes[i].set_ylabel("count")
        annotate_outliers(axes[i], removed_trails[metric], label_x=1)

    plt.tight_layout()
    plt.savefig(save_path, dpi=300, bbox_inches='tight')
    plt.close()


def plot_rt_accuracy_summary(measures_per_condition, measures_per_condition_no_err, save_path):
    """
    Plots 3 boxplots showing:
    - Mean Initial RT
    - Initial Accuracy
    - Mean Initial RT (excluding error trials)

    Parameters:
    - measures_per_condition (dict): Per-participant condition summaries including 'overall' stats.
    - measures_per_condition_no_err (dict): Same, but excluding error trials.
    - save_path (str): Full path to save the plot image (including .png).
    """
    # Extract data
    mean_initial_times = pd.Series(
        [m.loc['overall', 'initial_RT_mean'] for m in measures_per_condition.values()],
        index=measures_per_condition.keys()
    )
    initial_accuracy = pd.Series(
        [m.loc['overall', 'initial_RT_accuracy'] for m in measures_per_condition.values()],
        index=measures_per_condition.keys()
    )
    mean_initial_times_no_err = pd.Series(
        [m.loc['overall', 'initial_RT_mean'] for m in measures_per_condition_no_err.values()],
        index=measures_per_condition_no_err.keys()
    )

    # Plot
    fig, axes = plt.subplots(1, 3, figsize=(15, 5))

    # Plot definitions
    data_to_plot = [
        (mean_initial_times, "Mean Initial RT", "Reaction Time (ms)"),
        (initial_accuracy, "Initial Accuracy", "Proportion Correct"),
        (mean_initial_times_no_err, "Mean Initial RT - Without Error Trials", "Reaction Time (ms)")
    ]

    for i, (data, title, ylabel) in enumerate(data_to_plot):
        axes[i].boxplot(data, showmeans=True, notch=True)
        axes[i].set_title(title)
        axes[i].set_ylabel(ylabel)
        annotate_outliers(axes[i], data, label_x=1)

    plt.tight_layout()
    plt.savefig(save_path, dpi=300, bbox_inches='tight')
    # plt.show()
    plt.close()


def plot_dd_scores_by_emotion(dd_final, save_path):
    """
    Plots boxplots of complete movement D-scores for Happy, Sad, and Angry conditions.

    Parameters:
    - dd_final (pd.DataFrame): DataFrame with 'Emotion' and 'complete_movement' columns.
    - save_path (str): Full path to save the output plot (including .png).
    """
    # Extract data
    emotions = ['HAP', 'SAD', 'ANG']
    emotion_labels = ['Happy', 'Sad', 'Angry']
    dd_scores = [dd_final.loc[dd_final['Emotion'] == emo, 'complete_movement'] for emo in emotions]

    # Plot
    fig, axes = plt.subplots(1, 3, figsize=(15, 5))

    for i, (data, label) in enumerate(zip(dd_scores, emotion_labels)):
        axes[i].boxplot(data, showmeans=True, notch=True)
        axes[i].set_title(label)
        axes[i].set_ylabel("dd score")
        annotate_outliers(axes[i], data, label_x=1)

    plt.tight_layout()
    plt.savefig(save_path, dpi=300, bbox_inches='tight')
    # plt.show()
    plt.close()
