#!/usr/bin/env python3
"""
Generate histograms of Total steps for each solving method
from the solver_steps table and save them as PNG images.

Also creates a single comparison plot showing all four methods
as smoothed KDE density curves on the same graph.
"""

import sqlite3
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import os

def main():
    db_path = 'mazes.db'
    if not os.path.exists(db_path):
        print(f"Database {db_path} not found!")
        return

    conn = sqlite3.connect(db_path)

    # Check if solver_steps table exists and has data
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='solver_steps'")
    if not cursor.fetchone():
        print("Table 'solver_steps' does not exist. Run batch_solver.py first.")
        conn.close()
        return

    df = pd.read_sql_query("SELECT * FROM solver_steps", conn)
    conn.close()

    if df.empty:
        print("No data found in solver_steps table. Run batch_solver.py first.")
        return

    methods = [
        ("right_hand", "Right-Hand Rule"),
        ("left_hand", "Left-Hand Rule"),
        ("alternate_left", "Alternate Left"),
        ("alternate_right", "Alternate Right"),
    ]

    output_dir = "histograms"
    os.makedirs(output_dir, exist_ok=True)

    print(f"Generating histograms for {len(df)} mazes...\n")

    for col, title in methods:
        steps = df[col]

        # Skip if all values are -1 (errors)
        if (steps == -1).all():
            print(f"Skipping {title}: no valid data.")
            continue

        # Filter out error values (-1)
        valid_steps = steps[steps >= 0]

        plt.figure(figsize=(10, 6))
        plt.hist(valid_steps, bins=50, color='steelblue', edgecolor='black', alpha=0.8)
        plt.title(f"Histogram of Total Steps - {title}", fontsize=14, fontweight='bold')
        plt.xlabel("Total Steps", fontsize=12)
        plt.ylabel("Number of Mazes", fontsize=12)
        plt.grid(True, alpha=0.3)

        # Add statistics
        mean_val = valid_steps.mean()
        median_val = valid_steps.median()
        plt.axvline(mean_val, color='red', linestyle='--', linewidth=2, label=f'Mean: {mean_val:.1f}')
        plt.axvline(median_val, color='green', linestyle='-.', linewidth=2, label=f'Median: {median_val:.1f}')
        plt.legend()

        filename = os.path.join(output_dir, f"histogram_{col}.png")
        plt.savefig(filename, dpi=150, bbox_inches='tight')
        plt.close()

        print(f"  Saved: {filename}  (mean={mean_val:.1f}, median={median_val:.1f}, n={len(valid_steps)})")

    # === Comparison plot: all four methods as smoothed density lines (KDE) ===
    print("\nGenerating comparison overlay plot with smoothing...")

    sns.set_style("whitegrid")

    colors = {
        "right_hand": "#e41a1c",      # red
        "left_hand": "#377eb8",       # blue
        "alternate_left": "#4daf4a",  # green
        "alternate_right": "#ff7f00", # orange
    }

    plt.figure(figsize=(12, 7))

    for col, title in methods:
        valid_steps = df[col][df[col] >= 0]
        if len(valid_steps) == 0:
            continue
        sns.kdeplot(
            data=valid_steps,
            color=colors[col],
            linewidth=2.5,
            label=f"{title} (mean={valid_steps.mean():.1f})",
            fill=False
        )

    plt.title("Comparison of Solving Methods (Smoothed Density)", fontsize=16, fontweight='bold')
    plt.xlabel("Total Steps", fontsize=13)
    plt.ylabel("Density", fontsize=13)
    plt.legend(title="Method", fontsize=10)
    plt.grid(True, alpha=0.3)

    comparison_file = os.path.join(output_dir, "comparison_all_methods.png")
    plt.savefig(comparison_file, dpi=150, bbox_inches='tight')
    plt.close()

    print(f"  Saved: {comparison_file}")

    print(f"\nAll histograms saved to ./{output_dir}/")


if __name__ == '__main__':
    main()
