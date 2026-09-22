import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from io import BytesIO

st.set_page_config(page_title="Rare Event g-Chart", page_icon="📈", layout="wide")
st.title("Rare Event g-Chart")
st.caption("Geometric control chart for monitoring days between rare events.")

def g_chart_limits(series):
    series = pd.Series(series).dropna()
    if len(series) == 0:
        return np.nan, np.nan, np.nan, np.nan
    g_bar = series.mean()
    p = 1 / (g_bar + 1)
    probability_limit = 0.99865
    ucl = np.log(1 - probability_limit) / np.log(1 - p)
    lcl = 0.0
    return g_bar, p, ucl, lcl

def figure_to_png(fig):
    buffer = BytesIO()
    fig.savefig(buffer, format="png", dpi=300, bbox_inches="tight")
    buffer.seek(0)
    return buffer

# DATA
st.sidebar.header("Data")
uploaded_file = st.sidebar.file_uploader("Upload event data", type=["csv"])

if uploaded_file is None:
    st.info("Upload a CSV file containing one row for each event.")
    st.markdown("""
### Expected format
The CSV needs at least one column containing the date of each event.

```text
event_date
2022-01-10
2022-02-03
2022-03-12
```

Additional columns are allowed.
""")
    st.stop()

try:
    df = pd.read_csv(uploaded_file)
except Exception as e:
    st.error(f"Could not read CSV file: {e}")
    st.stop()

if df.empty:
    st.error("The uploaded CSV contains no data.")
    st.stop()

st.sidebar.success(f"{len(df):,} rows loaded")
date_column = st.sidebar.selectbox("Event date column", options=df.columns.tolist())

df["event_date"] = pd.to_datetime(df[date_column], errors="coerce")
invalid_dates = df["event_date"].isna().sum()

if invalid_dates:
    st.warning(f"{invalid_dates} row(s) contained invalid dates and were excluded.")

df = df.dropna(subset=["event_date"]).sort_values("event_date").reset_index(drop=True)

if len(df) < 2:
    st.error("At least two valid event dates are required to construct a g-chart.")
    st.stop()

duplicates = df[df["event_date"].duplicated(keep=False)]
if not duplicates.empty:
    st.warning("Multiple events occurred on the same calendar date. These produce zero-day intervals.")
    with st.expander("View same-day events"):
        st.dataframe(duplicates, use_container_width=True, hide_index=True)

df["previous_event_date"] = df["event_date"].shift(1)
df["days_between"] = (df["event_date"] - df["previous_event_date"]).dt.days
g = df.dropna(subset=["days_between"]).copy()

# ANALYSIS
st.sidebar.header("Analysis")
use_intervention = st.sidebar.checkbox("Use an intervention date", value=False)
INTERVENTION_DATE = None

if use_intervention:
    intervention_date = st.sidebar.date_input(
        "Intervention date",
        value=df["event_date"].median().date(),
        min_value=df["event_date"].min().date(),
        max_value=df["event_date"].max().date()
    )
    INTERVENTION_DATE = pd.Timestamp(intervention_date)

# CUSTOMIZATION
st.sidebar.header("Chart Customization")
event_name = st.sidebar.text_input("Event name", value="Event", help="Examples: CLABSI, CAUTI, Patient Fall")
chart_title = st.sidebar.text_input("Chart title", value=f"{event_name} g-Chart")
chart_subtitle = st.sidebar.text_input("Chart subtitle", value="")
y_axis_label = st.sidebar.text_input("Y-axis label", value=f"Days Between {event_name}s")
x_axis_label = st.sidebar.text_input("X-axis label", value=f"{event_name} Date")

if use_intervention:
    intervention_label = st.sidebar.text_input("Intervention label", value="Intervention")
else:
    intervention_label = "Intervention"

st.sidebar.subheader("Chart Elements")
show_centerline = st.sidebar.checkbox("Show centerline", value=True)
show_control_limits = st.sidebar.checkbox("Show control limits", value=True)
show_special_cause = st.sidebar.checkbox("Show special-cause markers", value=True)
show_grid = st.sidebar.checkbox("Show horizontal grid", value=True)

display_title = f"{chart_title}\n{chart_subtitle}" if chart_subtitle.strip() else chart_title

# SUMMARY
st.subheader("Data Summary")
c1, c2, c3 = st.columns(3)
c1.metric("Events", f"{len(df):,}")
c2.metric("Intervals", f"{len(g):,}")
c3.metric("Date Range", f"{df['event_date'].min().date()} to {df['event_date'].max().date()}")

if not use_intervention:
    CL, p, UCL, LCL = g_chart_limits(g["days_between"])
    g["special_cause"] = (g["days_between"] > UCL) | (g["days_between"] < LCL)
    special = g[g["special_cause"]]

    st.subheader("Process Summary")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Mean Days Between Events", f"{CL:.1f}")
    c2.metric("Daily Event Probability", f"{p:.5f}")
    c3.metric("Upper Control Limit", f"{UCL:.1f}")
    c4.metric("Lower Control Limit", f"{LCL:.1f}")

    st.subheader("g-Chart")
    fig, ax = plt.subplots(figsize=(14, 7))
    ax.plot(g["event_date"], g["days_between"], marker="o", linewidth=1.5, markersize=6,
            label=f"Days between {event_name.lower()}s")
    chart_start, chart_end = g["event_date"].min(), g["event_date"].max()

    if show_centerline:
        ax.hlines(CL, chart_start, chart_end, linewidth=2.5, label=f"CL = {CL:.1f} days")
    if show_control_limits:
        ax.hlines(UCL, chart_start, chart_end, linestyle="--", linewidth=1.5, label=f"UCL = {UCL:.1f} days")
        ax.hlines(LCL, chart_start, chart_end, linestyle="--", linewidth=1.5, label="LCL = 0")
    if show_special_cause and not special.empty:
        ax.scatter(special["event_date"], special["days_between"], marker="*", s=180, zorder=6, label="Special cause")

    ax.set_title(display_title, fontsize=16)
    ax.set_xlabel(x_axis_label)
    ax.set_ylabel(y_axis_label)
    ax.set_ylim(bottom=0)
    if show_grid:
        ax.grid(axis="y", alpha=0.25)
    ax.legend(loc="upper left", bbox_to_anchor=(1.02, 1))
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%b %Y"))
    fig.autofmt_xdate()
    plt.tight_layout()
    st.pyplot(fig)

    st.download_button("Download Chart (PNG)", figure_to_png(fig), "g_chart.png", "image/png")
    plt.close(fig)

    results = pd.DataFrame({
        "Period": ["Overall"],
        "Intervals": [len(g)],
        "Mean Days Between Events": [CL],
        "Daily Event Probability": [p],
        "UCL": [UCL],
        "LCL": [LCL],
        "Special Cause Points": [g["special_cause"].sum()]
    })
    st.download_button("Download Summary Results (CSV)", results.to_csv(index=False).encode("utf-8"),
                       "g_chart_summary.csv", "text/csv")

    if not special.empty:
        st.subheader("Special-Cause Observations")
        st.dataframe(special[["previous_event_date", "event_date", "days_between"]],
                     use_container_width=True, hide_index=True)

    with st.expander("View interval data"):
        st.dataframe(g[["previous_event_date", "event_date", "days_between", "special_cause"]],
                     use_container_width=True, hide_index=True)

    st.download_button(
        "Download Interval Data (CSV)",
        g[["previous_event_date", "event_date", "days_between", "special_cause"]].to_csv(index=False).encode("utf-8"),
        "g_chart_intervals.csv", "text/csv"
    )

else:
    g["period"] = np.select(
        [g["event_date"] < INTERVENTION_DATE, g["previous_event_date"] >= INTERVENTION_DATE],
        ["Pre-intervention", "Post-intervention"],
        default="Transition"
    )

    pre = g[g["period"] == "Pre-intervention"].copy()
    post = g[g["period"] == "Post-intervention"].copy()
    transition = g[g["period"] == "Transition"].copy()

    if len(pre) == 0:
        st.error("There are no complete pre-intervention intervals.")
        st.stop()
    if len(post) == 0:
        st.error("There are no complete post-intervention intervals.")
        st.stop()

    CL_pre, p_pre, UCL_pre, LCL_pre = g_chart_limits(pre["days_between"])
    CL_post, p_post, UCL_post, LCL_post = g_chart_limits(post["days_between"])

    absolute_change = CL_post - CL_pre
    percent_change = ((CL_post - CL_pre) / CL_pre) * 100
    ratio = CL_post / CL_pre

    pre["special_cause"] = (pre["days_between"] > UCL_pre) | (pre["days_between"] < LCL_pre)
    post["special_cause"] = (post["days_between"] > UCL_post) | (post["days_between"] < LCL_post)
    pre_special = pre[pre["special_cause"]]
    post_special = post[post["special_cause"]]

    st.subheader("Pre/Post Intervention Summary")
    st.write(f"**Intervention:** {intervention_label}  \n**Intervention date:** {INTERVENTION_DATE.date()}")

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Pre Mean Days", f"{CL_pre:.1f}")
    c2.metric("Post Mean Days", f"{CL_post:.1f}", delta=f"{percent_change:.1f}%")
    c3.metric("Absolute Change", f"{absolute_change:.1f} days")
    c4.metric("Post / Pre Ratio", f"{ratio:.2f}")

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Pre UCL", f"{UCL_pre:.1f}")
    c2.metric("Post UCL", f"{UCL_post:.1f}")
    c3.metric("Pre Event Probability", f"{p_pre:.5f}")
    c4.metric("Post Event Probability", f"{p_post:.5f}")

    st.caption(f"Pre-intervention intervals: {len(pre)} | Post-intervention intervals: {len(post)} | Transition intervals: {len(transition)}")

    if not transition.empty:
        st.info("The interval crossing the intervention date is displayed on the chart but excluded from both pre- and post-intervention centerline and control-limit calculations.")

    st.subheader("g-Chart")
    fig, ax = plt.subplots(figsize=(14, 7))
    ax.plot(pre["event_date"], pre["days_between"], marker="o", linewidth=1.5, markersize=6, label="Pre-intervention")
    ax.plot(post["event_date"], post["days_between"], marker="o", linewidth=1.5, markersize=6, label="Post-intervention")

    if not transition.empty:
        ax.scatter(transition["event_date"], transition["days_between"], marker="D", s=90, zorder=5, label="Transition interval")

    pre_start, post_end = pre["event_date"].min(), post["event_date"].max()

    if show_centerline:
        ax.hlines(CL_pre, pre_start, INTERVENTION_DATE, linewidth=2.5, label=f"Pre CL = {CL_pre:.1f} days")
        ax.hlines(CL_post, INTERVENTION_DATE, post_end, linewidth=2.5, label=f"Post CL = {CL_post:.1f} days")

    if show_control_limits:
        ax.hlines(UCL_pre, pre_start, INTERVENTION_DATE, linestyle="--", linewidth=1.5, label=f"Pre UCL = {UCL_pre:.1f}")
        ax.hlines(LCL_pre, pre_start, INTERVENTION_DATE, linestyle="--", linewidth=1.5)
        ax.hlines(UCL_post, INTERVENTION_DATE, post_end, linestyle="--", linewidth=1.5, label=f"Post UCL = {UCL_post:.1f}")
        ax.hlines(LCL_post, INTERVENTION_DATE, post_end, linestyle="--", linewidth=1.5)

    ax.axvline(INTERVENTION_DATE, linestyle=":", linewidth=2)
    ax.text(INTERVENTION_DATE, 0.97, f" {intervention_label}",
            transform=ax.get_xaxis_transform(), rotation=90, va="top", ha="right")

    if show_special_cause:
        if not pre_special.empty:
            ax.scatter(pre_special["event_date"], pre_special["days_between"], marker="*", s=180, zorder=6, label="Special cause")
        if not post_special.empty:
            ax.scatter(post_special["event_date"], post_special["days_between"], marker="*", s=180, zorder=6)

    ax.set_title(display_title, fontsize=16)
    ax.set_xlabel(x_axis_label)
    ax.set_ylabel(y_axis_label)
    ax.set_ylim(bottom=0)
    if show_grid:
        ax.grid(axis="y", alpha=0.25)
    ax.legend(loc="upper left", bbox_to_anchor=(1.02, 1))
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%b %Y"))
    fig.autofmt_xdate()
    plt.tight_layout()
    st.pyplot(fig)

    st.download_button("Download Chart (PNG)", figure_to_png(fig), "g_chart_pre_post.png", "image/png")
    plt.close(fig)

    st.subheader("Phase Statistics")
    results = pd.DataFrame({
        "Period": ["Pre-intervention", "Post-intervention"],
        "Intervals": [len(pre), len(post)],
        "Mean Days Between Events": [CL_pre, CL_post],
        "Daily Event Probability": [p_pre, p_post],
        "UCL": [UCL_pre, UCL_post],
        "LCL": [LCL_pre, LCL_post],
        "Special Cause Points": [pre["special_cause"].sum(), post["special_cause"].sum()]
    })

    st.dataframe(
        results.style.format({
            "Mean Days Between Events": "{:.2f}",
            "Daily Event Probability": "{:.5f}",
            "UCL": "{:.2f}",
            "LCL": "{:.2f}"
        }),
        use_container_width=True,
        hide_index=True
    )

    st.download_button("Download Summary Results (CSV)", results.to_csv(index=False).encode("utf-8"),
                       "g_chart_summary.csv", "text/csv")

    if not transition.empty:
        with st.expander("View transition interval"):
            st.dataframe(transition[["previous_event_date", "event_date", "days_between"]],
                         use_container_width=True, hide_index=True)

    all_special = pd.concat([
        pre_special.assign(phase="Pre-intervention"),
        post_special.assign(phase="Post-intervention")
    ], ignore_index=True)

    if not all_special.empty:
        st.subheader("Special-Cause Observations")
        st.dataframe(all_special[["phase", "previous_event_date", "event_date", "days_between"]],
                     use_container_width=True, hide_index=True)

    interval_display = pd.concat([pre, transition, post]).sort_values("event_date")

    with st.expander("View all interval data"):
        st.dataframe(interval_display[["previous_event_date", "event_date", "days_between", "period"]],
                     use_container_width=True, hide_index=True)

    st.download_button(
        "Download Interval Data (CSV)",
        interval_display[["previous_event_date", "event_date", "days_between", "period"]].to_csv(index=False).encode("utf-8"),
        "g_chart_intervals.csv", "text/csv"
    )

with st.expander("View uploaded data"):
    st.dataframe(df, use_container_width=True, hide_index=True)
