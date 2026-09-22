# G-Chart UTMC

**Rare Event Statistical Process Control**

G-Chart UTMC is a Streamlit application for statistical process control (SPC) monitoring of infrequent events using the geometric distribution. It is designed primarily for healthcare quality improvement, infection prevention, and patient-safety applications where conventional rate-based control charts may be less informative because events occur infrequently.

Rather than aggregating events into fixed reporting periods, the application measures the **number of days between consecutive events**. Longer intervals represent longer event-free periods, making the g-chart useful for monitoring uncommon adverse outcomes and evaluating changes in process performance over time.

## Features

- Upload event-level data from a CSV file
- Select the event-date field within the application
- Automatically calculate days between consecutive events
- Construct geometric statistical process control limits
- Use a strict **0.99865 cumulative probability limit** for the upper control limit
- Analyze a single process or specify an intervention date
- Calculate separate pre- and post-intervention centerlines and control limits
- Identify and display the **transition interval** spanning an intervention
- Detect observations outside geometric control limits
- Compare mean days between events before and after an intervention
- Estimate the corresponding daily event probability
- Customize event name, chart title, subtitle, and axis labels
- Toggle centerlines, control limits, special-cause markers, and grid lines
- Export charts as 300-dpi PNG files
- Export summary statistics and interval-level data as CSV files

## Pre/Post Intervention Analysis

When an intervention date is specified, event-to-event intervals are classified as:

- **Pre-intervention** — the entire interval occurred before the intervention.
- **Transition** — the event-to-event interval spans the intervention date.
- **Post-intervention** — the entire interval occurred after the intervention.

The transition interval is displayed on the g-chart but excluded from estimation of both the pre- and post-intervention centerlines and control limits.

A g-chart observation represents the complete elapsed time between two consecutive events. A transition interval contains time under both the pre- and post-intervention processes and therefore cannot be attributed exclusively to either phase. The application retains the transition interval as part of the observed process history without allowing it to influence either phase-specific parameter estimate.

## Statistical Approach

For observed days between events, the mean interval is:

`ḡ = (1/n) Σ gᵢ`

The geometric event probability is estimated as:

`p̂ = 1 / (ḡ + 1)`

The upper control limit is derived from the geometric distribution using a cumulative probability of **0.99865**:

`UCL = ln(1 - 0.99865) / ln(1 - p̂)`

The lower control limit is truncated at zero because negative event-free intervals are not possible.

When an intervention is specified, these parameters are estimated independently for the pre- and post-intervention phases, with the transition interval excluded from both calculations.

## Why Use a g-Chart?

Traditional surveillance often reports rare events as monthly or quarterly rates. When events are uncommon, this can result in long sequences of zero-event reporting periods and may obscure information contained in the actual time between events.

A g-chart instead asks:

> **How long did the process operate before the next event occurred?**

This preserves event-to-event information without requiring rare events to be aggregated into arbitrary fixed reporting periods.

For adverse events, an increase in the mean number of days between events represents a longer event-free period and may indicate improvement in process performance.

## Potential Applications

G-Chart UTMC can be used to monitor rare events such as:

- Central line-associated bloodstream infections (CLABSI)
- Catheter-associated urinary tract infections (CAUTI)
- Ventilator-associated events
- Surgical site infections
- Patient falls with injury
- Serious medication errors
- Pressure injuries
- Device complications
- Sentinel events
- Other uncommon patient-safety or quality events

Although designed with healthcare quality improvement in mind, the geometric approach can be applied to other processes in which the outcome of interest is an infrequent event.

## Important Interpretation

A change in the g-chart following an intervention demonstrates a **temporal change in process behavior**. The chart alone does not establish that the intervention caused the observed change.

Results should be interpreted alongside the intervention design, implementation timeline, surveillance definitions, exposure opportunities, other process changes, and relevant clinical or operational context.

## Input Data

At minimum, the CSV file must contain one column representing the date of each event:

```text
event_date
2024-01-10
2024-02-03
2024-03-12
2024-05-18
```

Additional columns may be included. The appropriate event-date column is selected within the application after upload.

Multiple legitimate events occurring on the same calendar date are retained and produce zero-day intervals.

## Requirements

G-Chart UTMC requires Python and:

- Streamlit
- pandas
- NumPy
- Matplotlib

Install the dependencies with:

```bash
pip install streamlit pandas numpy matplotlib
```

The included `requirements.txt` contains:

```text
streamlit
pandas
numpy
matplotlib
```

## Running Locally

From the application directory:

```bash
streamlit run g_chart_app.py
```

For example, in Git Bash:

```bash
cd /c/Users/wrbar/streamlit_apps
streamlit run g_chart_app.py
```

## Streamlit Community Cloud Deployment

The GitHub repository should contain at least:

```text
g_chart_app.py
requirements.txt
README.md
```

In Streamlit Community Cloud, select the GitHub repository, the `main` branch, and `g_chart_app.py` as the application entry point.

## Purpose

G-Chart UTMC provides quality-improvement professionals, infection prevention teams, patient-safety programs, researchers, and analysts with an accessible method for monitoring rare events using geometric statistical process control.

The application is intended as an analytical and quality-improvement tool. Results should be interpreted within the clinical, operational, and surveillance context in which the events occurred.
