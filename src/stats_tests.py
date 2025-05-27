import os.path
import pandas as pd
import scipy.stats as stats
import pingouin as pg
import scikit_posthocs as sp
import numpy as np
import matplotlib.pyplot as plt


def analyze_rt_accuracy_tradeoff(samples, config, pairs=[("initial_RTs", "ACC_1"), ("movement_durations", "ACC_2")]):
    """
    Analyzes RT vs Accuracy trade-off using:
    - Normality and variance checks
    - ANOVA or Kruskal-Wallis per measure
    - Post-hoc comparisons (Tukey or Dunn)
    - Plots scatter plots for overlapping significant RT and ACC conditions (if exist)

    Parameters:
    - samples (dict): Keys are measures names, values are DataFrames with columns = conditions, rows = participants.
    - pairs (list of tuples): Pairs of (RT_measure_name, ACC_measure_name) to be tested together.

    Returns:
    - posthoc_results (dict): Dictionary of significant conditions per measure from post-hoc tests.
    """

    # Store results for each statistical test
    is_normal = {}        # Will store whether data is normally distributed per measure (1.0 = yes)
    are_var_eq = {}       # Will store whether variance is equal across conditions (True/False)
    test_result = {}      # Will store p-values
    is_significant = {}   # Will store whether the overall effect is significant per measure (True/False)
    posthoc_results = {}  # Will store significant condition names per measure

    # 1. Check normality using Shapiro-Wilk test (per condition)
    for measure, df in samples.items():  # Iterate over the measures
        # Check how many conditions are normally distributed
        is_normal[measure] = np.mean([stats.shapiro(df[col])[1] >= 0.05 for col in df.columns])

    # 2. Check variance equality using Levene's test - Are the variances of all 8 conditions equal?
    for measure, df in samples.items():  # Iterate over the measures
        stat, p = stats.levene(*[df[col] for col in df.columns])
        are_var_eq[measure] = p >= 0.05  # True if p ≥ .05 → equal variances

    # 3. Run ANOVA or Kruskal-Wallis depending on assumptions
    for measure, df in samples.items():
        if is_normal[measure] == 1 and are_var_eq[measure]:
            print(f"Analyzing {measure} using ANOVA...")
            _, p_value = stats.f_oneway(*[df[col] for col in df.columns])
        else:
            print(f"Analyzing {measure} using Kruskal-Wallis test...")
            _, p_value = stats.kruskal(*[df[col] for col in df.columns])
        test_result[measure] = p_value

        if p_value < 0.05:
            print("There is a significant difference between at least two groups.")
            is_significant[measure] = True
        else:
            print("No significant difference between groups.")
            is_significant[measure] = False

    # 4. Post-hoc comparisons for each RT-ACC pair that was significant
    for rt, acc in pairs:
        if is_significant.get(rt, 0) and is_significant.get(acc, 0):
            print(f"\nPerforming post-hoc tests for {rt} and {acc}...")

            for measure in [rt, acc]:
                df_long = samples[measure].melt(var_name="Condition", value_name="Value")

                if is_normal[measure] == 1 and are_var_eq[measure]:
                    # Use Tukey HSD if assumptions met
                    print(f"Using Tukey's HSD for {measure} (ANOVA was used).")
                    tukey = pg.pairwise_tukey(data=df_long, dv="Value", between="Condition")
                    sig = tukey[tukey["p-tukey"] < 0.05]
                    posthoc_results[measure] = set(sig["A"]).union(set(sig["B"]))
                else:
                    # Use Dunn's test if assumptions violated
                    print(f"Using Dunn’s test for {measure} (Kruskal-Wallis was used).")
                    dunn = sp.posthoc_dunn(df_long, val_col="Value", group_col="Condition", p_adjust="bonferroni")
                    posthoc_results[measure] = {
                        i for i in dunn.index for j in dunn.columns
                        if i != j and dunn.loc[i, j] < 0.05
                    }
        else:
            print(f"\nNo single condition is significantly different in both {rt} and {acc}.")

    # 5. Find and visualize overlapping significant RT and ACC conditions
    save_path = os.path.join(config["plots_dir"], "rt_acc_tradeoff.png")
    for rt, acc in pairs:
        if rt in posthoc_results and acc in posthoc_results:
            common_conditions = posthoc_results[rt].intersection(posthoc_results[acc])

            if common_conditions:
                print(f"\nAbnormal condition detected in both {rt} and {acc}: {common_conditions}")
                for condition in common_conditions:
                    plt.figure(figsize=(6, 5))
                    plt.scatter(samples[rt][condition], samples[acc][condition], color='purple', alpha=0.7)
                    plt.xlabel("Reaction Time")
                    plt.ylabel("Accuracy")
                    plt.title(f"RT vs ACC Scatter Plot - {condition}")
                    plt.grid(True)
                    plt.savefig(save_path, dpi=300, bbox_inches='tight')
                    plt.show()
                    plt.close()

    # 6. Store the analysis process in Excel
    is_normal = pd.Series(is_normal, name="proportion of normal conditions")
    are_var_eq = pd.Series(are_var_eq, name="are all variances equal?")
    test_result = pd.Series(test_result, name="p value")
    posthoc_results = pd.Series(posthoc_results)

    output_path = os.path.join(config["results_dir"], "rt_acc_tradeoff.xlsx")
    with pd.ExcelWriter(output_path) as writer:
        is_normal.to_excel(writer, sheet_name="normality_check", index=True)
        are_var_eq.to_excel(writer, sheet_name="equal_of_variance_check", index=True)
        test_result.to_excel(writer, sheet_name="p_values", index=True)
        posthoc_results.to_excel(writer, sheet_name="post_hoc", index=True)
