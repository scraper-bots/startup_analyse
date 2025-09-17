#!/usr/bin/env python3
"""
Startup Data Analysis Script
Analyzes startup data from ideas.csv and generates insights with visualizations
"""

import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
import json
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

def load_and_explore_data():
    """Load the dataset and perform initial exploration"""
    print("Loading startup data...")

    # Load data with proper encoding
    df = pd.read_csv('ideas.csv', encoding='utf-8')

    print(f"Dataset shape: {df.shape}")
    print(f"Columns: {df.columns.tolist()}")

    # Basic info
    print("\n=== DATASET OVERVIEW ===")
    print(f"Total records: {len(df)}")
    print(f"Total columns: {len(df.columns)}")

    # Show first few records key info
    key_cols = ['title', 'status', 'type', 'createdDate', 'meta.tagline']
    available_cols = [col for col in key_cols if col in df.columns]

    if available_cols:
        print(f"\nFirst 5 records (key columns):")
        print(df[available_cols].head())

    return df

def analyze_startup_data(df):
    """Perform comprehensive analysis of startup data"""

    print("\n=== DATA QUALITY ANALYSIS ===")

    # Check for missing values
    missing_data = df.isnull().sum()
    print("Missing values per column:")
    print(missing_data[missing_data > 0].sort_values(ascending=False))

    # Convert createdDate to datetime
    if 'createdDate' in df.columns:
        df['createdDate'] = pd.to_datetime(df['createdDate'], unit='ms', errors='coerce')
        df['year'] = df['createdDate'].dt.year
        df['month'] = df['createdDate'].dt.month
        df['quarter'] = df['createdDate'].dt.quarter

    print(f"\nDate range: {df['createdDate'].min()} to {df['createdDate'].max()}")

    return df

def extract_insights(df):
    """Extract meaningful insights from the data"""

    insights = {}

    print("\n=== STARTUP INSIGHTS ===")

    # 1. Status distribution
    if 'status' in df.columns:
        status_counts = df['status'].value_counts()
        insights['status_distribution'] = status_counts
        print(f"\nStartup Status Distribution:")
        for status, count in status_counts.items():
            percentage = (count / len(df)) * 100
            print(f"  {status}: {count} ({percentage:.1f}%)")

    # 2. Submissions over time
    if 'year' in df.columns:
        yearly_counts = df['year'].value_counts().sort_index()
        insights['yearly_submissions'] = yearly_counts
        print(f"\nSubmissions by Year:")
        for year, count in yearly_counts.items():
            print(f"  {int(year)}: {count} startups")

    # 3. Type analysis
    if 'type' in df.columns:
        type_counts = df['type'].value_counts()
        insights['type_distribution'] = type_counts
        print(f"\nIdea Types:")
        for idea_type, count in type_counts.items():
            print(f"  {idea_type}: {count}")

    # 4. Business model analysis
    if 'meta.businessmodeldescription' in df.columns:
        business_models = df['meta.businessmodeldescription'].dropna()
        insights['business_models_count'] = len(business_models)
        print(f"\nBusiness Models Described: {len(business_models)} out of {len(df)}")

    # 5. Problem-solution analysis
    if 'meta.problemdescription' in df.columns:
        problems = df['meta.problemdescription'].dropna()
        insights['problems_identified'] = len(problems)
        print(f"Problems Identified: {len(problems)} out of {len(df)}")

    # 6. Value proposition analysis
    if 'meta.valuepropdescription' in df.columns:
        value_props = df['meta.valuepropdescription'].dropna()
        insights['value_props'] = len(value_props)
        print(f"Value Propositions: {len(value_props)} out of {len(df)}")

    return insights

def create_visualizations(df, insights):
    """Create visualizations and save as image files"""

    print("\n=== CREATING VISUALIZATIONS ===")

    # Set style
    plt.style.use('seaborn-v0_8')
    sns.set_palette("husl")

    # Create figure with subplots
    fig = plt.figure(figsize=(20, 24))

    # 1. Status Distribution Pie Chart
    if 'status_distribution' in insights:
        plt.subplot(3, 2, 1)
        status_data = insights['status_distribution']
        colors = plt.cm.Set3(np.linspace(0, 1, len(status_data)))
        wedges, texts, autotexts = plt.pie(status_data.values, labels=status_data.index,
                                          autopct='%1.1f%%', colors=colors, startangle=90)
        plt.title('Startup Status Distribution', fontsize=14, fontweight='bold')

        # Make percentage text bold and larger
        for autotext in autotexts:
            autotext.set_color('white')
            autotext.set_fontweight('bold')
            autotext.set_fontsize(10)

    # 2. Submissions Over Time
    if 'yearly_submissions' in insights:
        plt.subplot(3, 2, 2)
        yearly_data = insights['yearly_submissions']
        bars = plt.bar(yearly_data.index, yearly_data.values, color='steelblue', alpha=0.7)
        plt.title('Startup Submissions by Year', fontsize=14, fontweight='bold')
        plt.xlabel('Year', fontsize=12)
        plt.ylabel('Number of Submissions', fontsize=12)
        plt.xticks(rotation=45)

        # Add value labels on bars
        for bar in bars:
            height = bar.get_height()
            plt.text(bar.get_x() + bar.get_width()/2., height,
                    f'{int(height)}', ha='center', va='bottom', fontweight='bold')

    # 3. Monthly Submissions Heatmap
    if 'month' in df.columns and 'year' in df.columns:
        plt.subplot(3, 2, 3)
        monthly_pivot = df.groupby(['year', 'month']).size().unstack(fill_value=0)
        sns.heatmap(monthly_pivot, annot=True, fmt='d', cmap='YlOrRd',
                   cbar_kws={'label': 'Number of Submissions'})
        plt.title('Startup Submissions Heatmap (Year vs Month)', fontsize=14, fontweight='bold')
        plt.xlabel('Month', fontsize=12)
        plt.ylabel('Year', fontsize=12)

    # 4. Type Distribution
    if 'type_distribution' in insights:
        plt.subplot(3, 2, 4)
        type_data = insights['type_distribution']
        bars = plt.bar(range(len(type_data)), type_data.values, color='coral', alpha=0.7)
        plt.title('Idea Type Distribution', fontsize=14, fontweight='bold')
        plt.xlabel('Type', fontsize=12)
        plt.ylabel('Count', fontsize=12)
        plt.xticks(range(len(type_data)), type_data.index, rotation=45)

        # Add value labels on bars
        for bar in bars:
            height = bar.get_height()
            plt.text(bar.get_x() + bar.get_width()/2., height,
                    f'{int(height)}', ha='center', va='bottom', fontweight='bold')

    # 5. Quarterly Trends
    if 'quarter' in df.columns and 'year' in df.columns:
        plt.subplot(3, 2, 5)
        quarterly_data = df.groupby(['year', 'quarter']).size().reset_index(name='count')
        quarterly_data['period'] = quarterly_data['year'].astype(str) + '-Q' + quarterly_data['quarter'].astype(str)

        plt.plot(quarterly_data['period'], quarterly_data['count'], marker='o',
                linewidth=2, markersize=6, color='darkgreen')
        plt.title('Quarterly Submission Trends', fontsize=14, fontweight='bold')
        plt.xlabel('Quarter', fontsize=12)
        plt.ylabel('Number of Submissions', fontsize=12)
        plt.xticks(rotation=45)
        plt.grid(True, alpha=0.3)

    # 6. Completion Metrics
    plt.subplot(3, 2, 6)
    completion_metrics = {
        'Business Model': insights.get('business_models_count', 0),
        'Problem Description': insights.get('problems_identified', 0),
        'Value Proposition': insights.get('value_props', 0)
    }

    categories = list(completion_metrics.keys())
    values = list(completion_metrics.values())
    total = len(df)
    percentages = [(v/total)*100 for v in values]

    bars = plt.bar(categories, percentages, color=['skyblue', 'lightcoral', 'lightgreen'], alpha=0.7)
    plt.title('Completion Rate of Key Startup Components', fontsize=14, fontweight='bold')
    plt.xlabel('Component', fontsize=12)
    plt.ylabel('Completion Rate (%)', fontsize=12)
    plt.xticks(rotation=45)

    # Add percentage labels on bars
    for i, bar in enumerate(bars):
        height = bar.get_height()
        plt.text(bar.get_x() + bar.get_width()/2., height,
                f'{height:.1f}%\n({values[i]})', ha='center', va='bottom', fontweight='bold')

    plt.tight_layout(pad=3.0)
    plt.savefig('startup_analysis_charts.png', dpi=300, bbox_inches='tight')
    print("Charts saved as: startup_analysis_charts.png")

    # Create a summary statistics chart
    fig2, ax = plt.subplots(figsize=(12, 8))

    # Summary statistics
    summary_data = {
        'Total Startups': len(df),
        'Approved': insights['status_distribution'].get('APPROVED', 0) if 'status_distribution' in insights else 0,
        'Years Active': len(df['year'].dropna().unique()) if 'year' in df.columns else 0,
        'Avg per Year': len(df) // len(df['year'].dropna().unique()) if 'year' in df.columns and len(df['year'].dropna().unique()) > 0 else 0
    }

    categories = list(summary_data.keys())
    values = list(summary_data.values())

    bars = ax.bar(categories, values, color=['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4'], alpha=0.8)
    ax.set_title('Startup Ecosystem Summary Statistics', fontsize=16, fontweight='bold', pad=20)
    ax.set_ylabel('Count', fontsize=12)

    # Add value labels on bars
    for bar in bars:
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., height,
                f'{int(height)}', ha='center', va='bottom', fontweight='bold', fontsize=12)

    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig('startup_summary_stats.png', dpi=300, bbox_inches='tight')
    print("Summary chart saved as: startup_summary_stats.png")

    plt.close('all')

def generate_detailed_insights(df, insights):
    """Generate detailed textual insights"""

    detailed_insights = []

    # Overall statistics
    detailed_insights.append(f"## Overall Statistics")
    detailed_insights.append(f"- **Total Startups Analyzed**: {len(df)}")

    if 'status_distribution' in insights:
        approved = insights['status_distribution'].get('APPROVED', 0)
        approval_rate = (approved / len(df)) * 100
        detailed_insights.append(f"- **Approval Rate**: {approval_rate:.1f}% ({approved} out of {len(df)})")

    if 'yearly_submissions' in insights:
        yearly_data = insights['yearly_submissions']
        peak_year = yearly_data.idxmax()
        peak_count = yearly_data.max()
        detailed_insights.append(f"- **Peak Submission Year**: {int(peak_year)} with {peak_count} startups")

        # Growth analysis
        if len(yearly_data) > 1:
            first_year, last_year = yearly_data.index.min(), yearly_data.index.max()
            first_count, last_count = yearly_data[first_year], yearly_data[last_year]
            if first_count > 0:
                growth_rate = ((last_count - first_count) / first_count) * 100
                detailed_insights.append(f"- **Growth Rate**: {growth_rate:.1f}% from {int(first_year)} to {int(last_year)}")

    # Business readiness analysis
    detailed_insights.append(f"\n## Business Readiness Analysis")
    total_startups = len(df)

    if 'business_models_count' in insights:
        bm_rate = (insights['business_models_count'] / total_startups) * 100
        detailed_insights.append(f"- **Business Model Definition**: {bm_rate:.1f}% of startups have defined business models")

    if 'problems_identified' in insights:
        prob_rate = (insights['problems_identified'] / total_startups) * 100
        detailed_insights.append(f"- **Problem Identification**: {prob_rate:.1f}% of startups have clearly identified problems")

    if 'value_props' in insights:
        vp_rate = (insights['value_props'] / total_startups) * 100
        detailed_insights.append(f"- **Value Proposition**: {vp_rate:.1f}% of startups have defined value propositions")

    # Recommendations
    detailed_insights.append(f"\n## Key Recommendations")

    if 'status_distribution' in insights:
        approved_rate = (insights['status_distribution'].get('APPROVED', 0) / total_startups) * 100
        if approved_rate < 50:
            detailed_insights.append("- **Focus on Quality**: Low approval rate suggests need for better startup preparation and mentoring")
        else:
            detailed_insights.append("- **Strong Pipeline**: High approval rate indicates effective filtering and preparation processes")

    detailed_insights.append("- **Encourage Complete Submissions**: Startups with complete business models, problem definitions, and value propositions are more likely to succeed")
    detailed_insights.append("- **Seasonal Planning**: Consider submission timing patterns for better resource allocation")

    return detailed_insights

def main():
    """Main analysis function"""

    # Load and explore data
    df = load_and_explore_data()

    # Analyze data quality and clean
    df = analyze_startup_data(df)

    # Extract insights
    insights = extract_insights(df)

    # Create visualizations
    create_visualizations(df, insights)

    # Generate detailed insights
    detailed_insights = generate_detailed_insights(df, insights)

    # Save insights to text file
    with open('startup_insights.txt', 'w', encoding='utf-8') as f:
        f.write('\n'.join(detailed_insights))

    print("\n=== ANALYSIS COMPLETE ===")
    print("Generated files:")
    print("- startup_analysis_charts.png")
    print("- startup_summary_stats.png")
    print("- startup_insights.txt")

    return df, insights, detailed_insights

if __name__ == "__main__":
    main()