#!/usr/bin/env python3
"""
Fix the status distribution chart with better label positioning
"""

import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np

def fix_status_chart():
    # Load data
    df = pd.read_csv('ideas.csv', encoding='utf-8')

    # Set style
    plt.style.use('seaborn-v0_8')

    # Create figure with larger size
    plt.figure(figsize=(12, 10))

    status_counts = df['status'].value_counts()

    # Define colors for better visibility
    colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FECA57', '#FF9FF3', '#54A0FF', '#5F27CD']

    # Create pie chart with better formatting
    wedges, texts, autotexts = plt.pie(
        status_counts.values,
        labels=None,  # Remove labels from pie to avoid overlap
        autopct='%1.1f%%',
        colors=colors[:len(status_counts)],
        startangle=90,
        pctdistance=0.85,  # Move percentages closer to edge
        explode=[0.05 if i < 4 else 0.02 for i in range(len(status_counts))]  # Explode larger slices more
    )

    # Format percentage text
    for autotext in autotexts:
        autotext.set_color('white')
        autotext.set_fontweight('bold')
        autotext.set_fontsize(12)
        autotext.set_bbox(dict(boxstyle="round,pad=0.3", facecolor='black', alpha=0.7))

    # Create legend with counts and percentages
    legend_labels = []
    total = sum(status_counts.values)
    for status, count in status_counts.items():
        percentage = (count / total) * 100
        legend_labels.append(f'{status}: {count} ({percentage:.1f}%)')

    plt.legend(
        wedges,
        legend_labels,
        title="Startup Status",
        loc="center left",
        bbox_to_anchor=(1, 0, 0.5, 1),
        fontsize=11,
        title_fontsize=13
    )

    plt.title('Startup Status Distribution', fontsize=18, fontweight='bold', pad=30)

    # Equal aspect ratio ensures that pie is drawn as a circle
    plt.axis('equal')

    plt.tight_layout()
    plt.savefig('assets/status_distribution.png', dpi=300, bbox_inches='tight')
    plt.close()

    print("Fixed status distribution chart saved!")

    # Also create a horizontal bar chart as alternative
    plt.figure(figsize=(12, 8))

    # Sort by count for better visualization
    status_counts_sorted = status_counts.sort_values(ascending=True)

    # Create horizontal bar chart
    bars = plt.barh(range(len(status_counts_sorted)), status_counts_sorted.values,
                   color=colors[:len(status_counts_sorted)], alpha=0.8)

    plt.yticks(range(len(status_counts_sorted)), status_counts_sorted.index, fontsize=12)
    plt.xlabel('Number of Startups', fontsize=12)
    plt.title('Startup Status Distribution (Bar Chart)', fontsize=16, fontweight='bold', pad=20)

    # Add value labels on bars
    for i, bar in enumerate(bars):
        width = bar.get_width()
        percentage = (width / total) * 100
        plt.text(width + 5, bar.get_y() + bar.get_height()/2,
                f'{int(width)} ({percentage:.1f}%)',
                ha='left', va='center', fontweight='bold', fontsize=11)

    plt.grid(axis='x', alpha=0.3)
    plt.tight_layout()
    plt.savefig('assets/status_distribution_bars.png', dpi=300, bbox_inches='tight')
    plt.close()

    print("Alternative bar chart also created!")

if __name__ == "__main__":
    fix_status_chart()