# Approach-Avoidance Task (AAT) Analysis Pipeline

This repository provides a comprehensive pipeline for processing, analyzing, and visualizing data from an **Approach-Avoidance Task (AAT)** experiment. The pipeline includes robust data cleaning, reaction time (RT) and accuracy analysis, double-difference D-score computation, and statistical testing (including RT vs. accuracy trade-offs).

---

## Project Structure

```
noa-shalom-aat_analysis/
│
├── requirements.txt       # Python dependencies
├── config/                # YAML config files for the different versions (i.e., kids and adults)
│   ├── adults.yaml
│   └── kids.yaml
├── plots/                 # Output figures
├── raw_data/              # Input data (.txt files)
├── results/               # Final results and summary Excel files
└── src/                   # All processing scripts
    ├── analyze.py
    ├── config_loader.py
    ├── constants.py
    ├── load_data.py
    ├── main.py
    ├── preprocess.py
    ├── stats_tests.py
    └── visualization.py
```

---

## Getting Started

### Prerequisites

- Python 3.8+
- Recommended: Create a virtual environment.

### Installation

```bash
git clone https://github.com/yourusername/noa-shalom-aat_analysis.git
cd noa-shalom-aat_analysis
pip install -r requirements.txt
```

---

## Configuration

If needed, update `config/adults.yaml` and `config/kids.yaml` with the appropriate:

- Raw data directory
- Output directories for plots and results
- Participant ID formatting

---

## Running the Pipeline

The main entry point is `src/main.py`.

```bash
python src/main.py
```

This will:
- Load and clean raw participant data.
- Remove confusion trials and outliers.
- Compute RT and accuracy metrics per condition.
- Calculate double-difference (D) scores.
- Generate boxplots and summary stats.
- Export final results to Excel (`AAT_results_final.xlsx`).

Before running the script:
- Set the `config` variable in `main.py` to load either `config/adults.yaml` or `config/kids.yaml`, depending on the dataset you are analyzing.  
  The two configurations differ in thresholds, ID formats, and other parameters.

---

## Output

- `results/`: 
  - 'AAT_results_final.xlsx' includes per-condition RTs, accuracies, and D-scores.
  - 'removed_trials.xlsx' provides a summary of all data cleaning steps.
  - 'rt_acc_tradeoff.xlsx' contains information about the RT vs. accuracy trade-off analysis.
- `plots/`: 
  - Outliers count boxplots
  - RT and accuracy distributions
  - D-score comparisons by emotion
  - RT-accuracy trade-off analysis (if needed)

---

## Statistical Features

- Shapiro-Wilk and Levene’s tests for normality and variance.
- ANOVA or Kruskal-Wallis for comparing RT and accuracy across conditions.
- Post-hoc tests (Tukey HSD or Dunn’s test).
- Identification of experimental conditions with significant RT-accuracy conflicts.

---

## Contact

Maintained by **Noa Shalom**  
Email: *noaaaa21@gmail.com*  
GitHub: [@noa-shalom](https://github.com/noa-shalom)
