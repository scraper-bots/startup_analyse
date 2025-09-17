#!/usr/bin/env python3
"""
Complete Startup Data Analysis Script
Analyzes startup data from ideas.csv and generates all charts and insights
"""

import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
import os

def main():
    # Load data
    print("Loading startup data...")
    df = pd.read_csv('ideas.csv', encoding='utf-8')

    # Convert dates
    df['createdDate'] = pd.to_datetime(df['createdDate'], unit='ms', errors='coerce')
    df['year'] = df['createdDate'].dt.year
    df['month'] = df['createdDate'].dt.month
    df['quarter'] = df['createdDate'].dt.quarter

    # Create assets directory
    os.makedirs('assets', exist_ok=True)

    # Set style
    plt.style.use('seaborn-v0_8')

    print("Creating visualizations...")

    # 1. Status Distribution (Bar Chart)
    plt.figure(figsize=(12, 8))
    status_counts = df['status'].value_counts().sort_values(ascending=True)
    colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FECA57', '#FF9FF3', '#54A0FF', '#5F27CD']

    bars = plt.barh(range(len(status_counts)), status_counts.values,
                   color=colors[:len(status_counts)], alpha=0.8)

    plt.yticks(range(len(status_counts)), status_counts.index, fontsize=12)
    plt.xlabel('Number of Startups', fontsize=12)
    plt.title('Startup Status Distribution', fontsize=16, fontweight='bold', pad=20)

    total = sum(status_counts.values)
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

    # 2. Yearly Submissions
    plt.figure(figsize=(12, 6))
    yearly_counts = df['year'].value_counts().sort_index()
    bars = plt.bar(yearly_counts.index, yearly_counts.values, color='steelblue', alpha=0.8)
    plt.title('Startup Submissions by Year', fontsize=16, fontweight='bold', pad=20)
    plt.xlabel('Year', fontsize=12)
    plt.ylabel('Number of Submissions', fontsize=12)

    for bar in bars:
        height = bar.get_height()
        plt.text(bar.get_x() + bar.get_width()/2., height + 2,
                f'{int(height)}', ha='center', va='bottom', fontweight='bold')

    plt.grid(axis='y', alpha=0.3)
    plt.tight_layout()
    plt.savefig('assets/yearly_submissions.png', dpi=300, bbox_inches='tight')
    plt.close()

    # 3. Monthly Heatmap
    plt.figure(figsize=(12, 8))
    monthly_pivot = df.groupby(['year', 'month']).size().unstack(fill_value=0)
    sns.heatmap(monthly_pivot, annot=True, fmt='d', cmap='YlOrRd',
               cbar_kws={'label': 'Number of Submissions'})
    plt.title('Startup Submissions Heatmap (Year vs Month)', fontsize=16, fontweight='bold', pad=20)
    plt.xlabel('Month', fontsize=12)
    plt.ylabel('Year', fontsize=12)
    plt.tight_layout()
    plt.savefig('assets/monthly_heatmap.png', dpi=300, bbox_inches='tight')
    plt.close()

    # 4. Quarterly Trends
    plt.figure(figsize=(12, 6))
    quarterly_data = df.groupby(['year', 'quarter']).size().reset_index(name='count')
    quarterly_data['period'] = quarterly_data['year'].astype(str) + '-Q' + quarterly_data['quarter'].astype(str)

    plt.plot(quarterly_data['period'], quarterly_data['count'], marker='o',
            linewidth=3, markersize=8, color='darkgreen')
    plt.title('Quarterly Submission Trends', fontsize=16, fontweight='bold', pad=20)
    plt.xlabel('Quarter', fontsize=12)
    plt.ylabel('Number of Submissions', fontsize=12)
    plt.xticks(rotation=45)
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig('assets/quarterly_trends.png', dpi=300, bbox_inches='tight')
    plt.close()

    # 5. Business Readiness
    plt.figure(figsize=(10, 6))
    total = len(df)
    completion_metrics = {
        'Business Model': len(df['meta.businessmodeldescription'].dropna()),
        'Problem Description': len(df['meta.problemdescription'].dropna()),
        'Value Proposition': len(df['meta.valuepropdescription'].dropna())
    }

    categories = list(completion_metrics.keys())
    values = list(completion_metrics.values())
    percentages = [(v/total)*100 for v in values]

    bars = plt.bar(categories, percentages, color=['#FF6B6B', '#4ECDC4', '#45B7D1'], alpha=0.8)
    plt.title('Business Readiness: Completion Rates', fontsize=16, fontweight='bold', pad=20)
    plt.xlabel('Component', fontsize=12)
    plt.ylabel('Completion Rate (%)', fontsize=12)

    for i, bar in enumerate(bars):
        height = bar.get_height()
        plt.text(bar.get_x() + bar.get_width()/2., height + 1,
                f'{height:.1f}%\n({values[i]})', ha='center', va='bottom', fontweight='bold')

    plt.grid(axis='y', alpha=0.3)
    plt.tight_layout()
    plt.savefig('assets/business_readiness.png', dpi=300, bbox_inches='tight')
    plt.close()

    # 6. Summary Stats
    plt.figure(figsize=(12, 6))
    status_counts = df['status'].value_counts()
    summary_data = {
        'Total Startups': len(df),
        'Approved': status_counts.get('APPROVED', 0),
        'Alumni': status_counts.get('ALUMNI', 0),
        'Rejected': status_counts.get('REJECTED', 0)
    }

    categories = list(summary_data.keys())
    values = list(summary_data.values())

    bars = plt.bar(categories, values, color=['#2E86C1', '#28B463', '#F39C12', '#E74C3C'], alpha=0.8)
    plt.title('Startup Ecosystem Summary Statistics', fontsize=16, fontweight='bold', pad=20)
    plt.ylabel('Count', fontsize=12)

    for bar in bars:
        height = bar.get_height()
        plt.text(bar.get_x() + bar.get_width()/2., height + 5,
                f'{int(height)}', ha='center', va='bottom', fontweight='bold', fontsize=12)

    plt.grid(axis='y', alpha=0.3)
    plt.tight_layout()
    plt.savefig('assets/summary_statistics.png', dpi=300, bbox_inches='tight')
    plt.close()

    print("\nAnalysis complete! Generated charts:")
    print("- assets/status_distribution_bars.png")
    print("- assets/yearly_submissions.png")
    print("- assets/monthly_heatmap.png")
    print("- assets/quarterly_trends.png")
    print("- assets/business_readiness.png")
    print("- assets/summary_statistics.png")

if __name__ == "__main__":
    main()