import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
from datetime import datetime
from database import Complaint, ProcessStatus
import logging

class VisualizationManager:
    def __init__(self, db):
        self.db = db
        self.logger = logging.getLogger(__name__)

    def generate_complaint_dashboard(self):
        """Generate comprehensive visualizations of complaint data"""
        print("\n📊 Generating complaint visualizations...")
        
        complaints = self.db.get_all_complaints()
        if not complaints:
            print("ℹ️ No complaints found in database.")
            return
        
        # Convert to DataFrame for easier analysis
        data = []
        for complaint in complaints:
            data.append({
                'id': complaint.id,
                'category': complaint.complaint_category,
                'importance': complaint.importance_level.value if complaint.importance_level else 'Unknown',
                'status': complaint.processed.value,
                'received_at': complaint.received_at,
                'processed_at': complaint.processed_at
            })
        
        df = pd.DataFrame(data)
        
        # Set up the plotting style
        plt.style.use('seaborn-v0_8')
        fig, axes = plt.subplots(2, 2, figsize=(15, 12))
        fig.suptitle('Complaint Analysis Dashboard', fontsize=16, fontweight='bold')
        
        # 1. Complaint Categories Bar Chart
        if 'category' in df.columns and not df['category'].isna().all():
            category_counts = df['category'].value_counts()
            axes[0, 0].bar(range(len(category_counts)), category_counts.values, color='skyblue', alpha=0.7)
            axes[0, 0].set_title('Complaints by Category', fontweight='bold')
            axes[0, 0].set_xlabel('Category')
            axes[0, 0].set_ylabel('Number of Complaints')
            axes[0, 0].set_xticks(range(len(category_counts)))
            axes[0, 0].set_xticklabels(category_counts.index, rotation=45, ha='right')
            axes[0, 0].grid(True, alpha=0.3)
        else:
            axes[0, 0].text(0.5, 0.5, 'No category data available', ha='center', va='center', transform=axes[0, 0].transAxes)
            axes[0, 0].set_title('Complaints by Category', fontweight='bold')
        
        # 2. Importance Level Pie Chart
        if 'importance' in df.columns and not df['importance'].isna().all():
            importance_counts = df['importance'].value_counts()
            colors = ['#ff9999', '#66b3ff', '#99ff99', '#ffcc99']
            axes[0, 1].pie(importance_counts.values, labels=importance_counts.index, autopct='%1.1f%%', 
                          colors=colors[:len(importance_counts)], startangle=90)
            axes[0, 1].set_title('Complaints by Importance Level', fontweight='bold')
        else:
            axes[0, 1].text(0.5, 0.5, 'No importance data available', ha='center', va='center', transform=axes[0, 1].transAxes)
            axes[0, 1].set_title('Complaints by Importance Level', fontweight='bold')
        
        # 3. Processing Status Bar Chart
        if 'status' in df.columns and not df['status'].isna().all():
            status_counts = df['status'].value_counts()
            colors = ['#ff9999', '#66b3ff', '#99ff99']
            axes[1, 0].bar(range(len(status_counts)), status_counts.values, 
                          color=colors[:len(status_counts)], alpha=0.7)
            axes[1, 0].set_title('Complaints by Processing Status', fontweight='bold')
            axes[1, 0].set_xlabel('Status')
            axes[1, 0].set_ylabel('Number of Complaints')
            axes[1, 0].set_xticks(range(len(status_counts)))
            axes[1, 0].set_xticklabels(status_counts.index)
            axes[1, 0].grid(True, alpha=0.3)
        else:
            axes[1, 0].text(0.5, 0.5, 'No status data available', ha='center', va='center', transform=axes[1, 0].transAxes)
            axes[1, 0].set_title('Complaints by Processing Status', fontweight='bold')
        
        # 4. Complaints Over Time (Line Chart)
        if 'received_at' in df.columns and not df['received_at'].isna().all():
            df['date'] = pd.to_datetime(df['received_at']).dt.date
            daily_counts = df['date'].value_counts().sort_index()
            axes[1, 1].plot(range(len(daily_counts)), daily_counts.values, marker='o', linewidth=2, markersize=6)
            axes[1, 1].set_title('Complaints Received Over Time', fontweight='bold')
            axes[1, 1].set_xlabel('Days')
            axes[1, 1].set_ylabel('Number of Complaints')
            axes[1, 1].grid(True, alpha=0.3)
        else:
            axes[1, 1].text(0.5, 0.5, 'No date data available', ha='center', va='center', transform=axes[1, 1].transAxes)
            axes[1, 1].set_title('Complaints Received Over Time', fontweight='bold')
        
        plt.tight_layout()
        
        # Save the visualization
        filename = f'complaint_analysis_{datetime.now().strftime("%Y%m%d_%H%M%S")}.png'
        plt.savefig(filename, dpi=300, bbox_inches='tight')
        print(f"✅ Visualization saved as: {filename}")
        
        # Show the plot
        plt.show()
        
        # Print summary statistics
        self._print_summary_statistics(df)

    def _print_summary_statistics(self, df):
        """Print summary statistics for the visualization"""
        print(f"\n📈 Summary Statistics:")
        print(f"Total Complaints: {len(df)}")
        if 'category' in df.columns:
            print(f"Most Common Category: {df['category'].mode().iloc[0] if not df['category'].mode().empty else 'N/A'}")
        if 'importance' in df.columns:
            print(f"Most Common Importance Level: {df['importance'].mode().iloc[0] if not df['importance'].mode().empty else 'N/A'}")
        if 'status' in df.columns:
            print(f"Processing Status: {df['status'].value_counts().to_dict()}") 