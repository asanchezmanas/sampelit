# Experiment Details Guide

## Overview

The **Experiment Detail** page is the command center for analyzing individual A/B tests. It provides real-time metrics, statistical significance calculations, and visual trends to help you make data-driven decisions.

## Key Metrics

The dashboard highlights four critical metrics at the top:

1.  **Total Visitors**: The unique number of users who have been exposed to any variant of the experiment.
2.  **Conversions**: The total number of successful goal completions (e.g., sign-ups, purchases).
3.  **Conversion Rate**: The overall percentage of visitors who converted.
    *   *Calculation*: `(Conversions / Visitors) * 100`
4.  **Statistical Significance**: The probability that the difference between the winner and the control is not due to random chance. We use a Bayesian inference model.
    *   *Target*: We recommend waiting for **95%** significance before declaring a winner.

## Visualizations

### 1. Conversion Rate Over Time
*   **Type**: Gradient Area Chart
*   **Purpose**: Shows the cumulative conversion rate trend for each variant over the duration of the experiment.
*   **Interpretation**: Look for the lines to diverge. If the "Variant B" line consistently stays above "Control", it indicates a positive lift. The gradient styling emphasizes the volume of data.

### 2. Daily Conversions
*   **Type**: Bar Chart
*   **Purpose**: Displays the raw number of conversions per day.
*   **Interpretation**: This helps identify traffic spikes or specific days where performance changed drastically (e.g., due to a marketing email or weekend effect).

## Actions

*   **Pause**: Temporarily stops traffic allocation to the experiment. Users will see the Control version by default.
*   **Finalize**: Ends the experiment and permanently rolls out the winning variant to 100% of traffic.

## Variants Tab

The **Variants** tab provides a granular breakdown:
*   **Traffic Split**: How much traffic each variant is receiving (default is 50/50).
*   **Winner Badge**: Automatically appears when a variant reaches >95% significance with a positive lift.
