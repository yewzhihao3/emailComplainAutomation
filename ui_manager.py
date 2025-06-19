from database import ProcessStatus

class UIManager:
    def __init__(self):
        pass

    def show_menu(self):
        """Show the main menu"""
        print("\n🚀 Complaint Processing System - Main Menu")
        print("=" * 50)
        print("1. Load NEW complaints only")
        print("2. Process UNPROCESSED complaints only")
        print("3. Generate visualizations 📈")
        print("4. View database summary 📊")
        print("5. View sample complaints")
        print("6. Export complaints to CSV")
        print("7. Process PENDING & FAILED complaints 🔄")
        print("8. Mark ALL as unprocessed (reset status) ⚠️")
        print("9. Load and process ALL complaints (⚠️ full refresh)")
        print("10. Exit")
        print("-" * 50)

    def confirm_full_refresh(self):
        """Get confirmation for full refresh with strong warning"""
        print("\n⚠️  WARNING: FULL REFRESH OPERATION")
        print("=" * 50)
        print("This operation will:")
        print("• DELETE ALL existing complaint data from the database")
        print("• Load ALL complaints from Google Sheets")
        print("• Process ALL complaints with AI analysis")
        print("• This action cannot be undone!")
        print("=" * 50)
        
        # First confirmation
        confirm = input("\nAre you sure you want to proceed? (y/n): ").lower().strip()
        if confirm not in ['y', 'yes']:
            print("❌ Operation cancelled.")
            return False
        
        # Second confirmation with specific phrase
        print("\n⚠️  FINAL CONFIRMATION REQUIRED")
        print("To proceed, you must type exactly: 'Yes, I understand what am I doing'")
        print("This ensures you understand the consequences of this action.")
        
        phrase = input("\nType the confirmation phrase: ").strip()
        if phrase == "Yes, I understand what am I doing":
            print("✅ Confirmation received. Proceeding with full refresh...")
            return True
        else:
            print("❌ Incorrect phrase. Operation cancelled.")
            return False

    def confirm_reset_operation(self):
        """Get confirmation for reset operation with strong warning"""
        print("\n⚠️  WARNING: RESET OPERATION")
        print("=" * 50)
        print("This operation will:")
        print("• Reset ALL processed complaints back to pending status")
        print("• Clear all AI analysis results (root cause, solutions)")
        print("• This action cannot be undone!")
        print("=" * 50)
        
        # First confirmation
        confirm = input("\nAre you sure you want to reset all processed complaints? (y/n): ").lower().strip()
        if confirm not in ['y', 'yes']:
            print("❌ Operation cancelled.")
            return False
        
        # Second confirmation with specific phrase
        print("\n⚠️  FINAL CONFIRMATION REQUIRED")
        print("To proceed, you must type exactly: 'Yes, reset all processed complaints'")
        print("This ensures you understand the consequences of this action.")
        
        phrase = input("\nType the confirmation phrase: ").strip()
        if phrase == "Yes, reset all processed complaints":
            print("✅ Confirmation received. Proceeding with reset...")
            return True
        else:
            print("❌ Incorrect phrase. Operation cancelled.")
            return False

    def show_statistics(self, db):
        """Show current database statistics with enhanced details"""
        stats = db.get_database_stats()
        complaints = db.get_all_complaints()
        
        print("\n📊 Current Complaint Summary:")
        print("=" * 40)
        print(f"• Total: {stats['total']}")
        print(f"• Processed: {stats['successful']}")
        print(f"• Pending: {stats['pending']}")
        print(f"• Failed: {stats['failed']}")
        print(f"• Success Rate: {stats['processed_percentage']}%")
        
        # Calculate additional statistics
        if complaints:
            # Most common category
            categories = [c.complaint_category for c in complaints if c.complaint_category]
            if categories:
                from collections import Counter
                category_counts = Counter(categories)
                most_common_category = category_counts.most_common(1)[0][0]
                print(f"• Most common category: \"{most_common_category}\"")
            
            # Average importance level
            importance_levels = [c.importance_level.value for c in complaints if c.importance_level]
            if importance_levels:
                from collections import Counter
                importance_counts = Counter(importance_levels)
                most_common_importance = importance_counts.most_common(1)[0][0]
                print(f"• Most common importance level: {most_common_importance}")
            
            # Processing time statistics (if any complaints are processed)
            processed_complaints = [c for c in complaints if c.processed_at and c.received_at]
            if processed_complaints:
                import datetime
                processing_times = []
                for complaint in processed_complaints:
                    if complaint.processed_at and complaint.received_at:
                        processing_time = complaint.processed_at - complaint.received_at
                        processing_times.append(processing_time.total_seconds() / 3600)  # Convert to hours
                
                if processing_times:
                    avg_processing_time = sum(processing_times) / len(processing_times)
                    print(f"• Avg. processing time: {avg_processing_time:.1f} hours")
        
        print("=" * 40)
        
        # Ask if user wants to see a chart
        try:
            chart_choice = input("\n[Optional] Would you like to view this as a chart? (y/n): ").lower().strip()
            if chart_choice in ['y', 'yes']:
                self._generate_summary_chart(db, stats, complaints)
        except KeyboardInterrupt:
            print("\nChart generation cancelled.")
        except Exception as e:
            print(f"❌ Error generating chart: {e}")

    def _generate_summary_chart(self, db, stats, complaints):
        """Generate a summary chart for the statistics"""
        try:
            import matplotlib.pyplot as plt
            import pandas as pd
            import os
            from collections import Counter
            from datetime import datetime
            
            print("\n📈 Generating summary chart...")
            
            # Create charts folder if it doesn't exist
            charts_folder = "charts"
            if not os.path.exists(charts_folder):
                os.makedirs(charts_folder)
                print(f"📁 Created charts folder: {charts_folder}")
            
            # Create a simple but informative chart
            fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 6))
            fig.suptitle('Complaint Processing Summary', fontsize=16, fontweight='bold')
            
            # Chart 1: Processing Status Donut Chart (with enhancements)
            status_data = [stats['successful'], stats['pending'], stats['failed']]
            status_labels = ['Processed', 'Pending', 'Failed']
            colors = ['#2ecc71', '#f39c12', '#e74c3c']
            
            # Only show nonzero statuses
            filtered = [(label, value, color) for label, value, color in zip(status_labels, status_data, colors) if value > 0]
            if filtered:
                labels, values, pie_colors = zip(*filtered)
                wedges, texts, autotexts = ax1.pie(
                    values, labels=labels, autopct='%1.1f%%', colors=pie_colors, startangle=90, wedgeprops=dict(width=0.4)
                )
                # Add center label if only one status
                if len(values) == 1:
                    ax1.text(0, 0, f"{labels[0]}\n{values[0]}", ha='center', va='center', fontsize=16, fontweight='bold')
            else:
                ax1.text(0.5, 0.5, 'No data', ha='center', va='center', transform=ax1.transAxes, fontsize=14)
            ax1.set_title('Processing Status Distribution', fontweight='bold')
            
            # Chart 2: Category Distribution (if data available)
            categories = [c.complaint_category for c in complaints if c.complaint_category]
            if categories:
                category_counts = Counter(categories)
                # Show top 5 categories
                top_categories = category_counts.most_common(5)
                category_names = [cat[0] for cat in top_categories]
                category_values = [cat[1] for cat in top_categories]
                
                bars = ax2.bar(range(len(category_names)), category_values, color='skyblue', alpha=0.7)
                ax2.set_title('Top Complaint Categories', fontweight='bold')
                ax2.set_xlabel('Category')
                ax2.set_ylabel('Number of Complaints')
                ax2.set_xticks(range(len(category_names)))
                ax2.set_xticklabels(category_names, rotation=45, ha='right')
                ax2.grid(True, alpha=0.3)
                
                # Add value labels on bars
                for bar, value in zip(bars, category_values):
                    ax2.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.1, 
                            str(value), ha='center', va='bottom')
            else:
                ax2.text(0.5, 0.5, 'No category data available', ha='center', va='center', 
                        transform=ax2.transAxes, fontsize=12)
                ax2.set_title('Top Complaint Categories', fontweight='bold')
            
            plt.tight_layout()
            
            # Save the chart with timestamp
            timestamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
            filename = os.path.join(charts_folder, f'complaint_summary_{timestamp}.png')
            plt.savefig(filename, dpi=300, bbox_inches='tight')
            print(f"✅ Chart saved as: {filename}")
            
            # Show the plot
            plt.show()
            
        except ImportError:
            print("❌ Chart generation requires matplotlib. Please install it with: pip install matplotlib")
        except Exception as e:
            print(f"❌ Error generating chart: {e}")

    def show_sample_complaints(self, db):
        """Show sample complaints from the database and allow searching by COMP ID or ORDER ID"""
        complaints = db.get_all_complaints()
        
        if not complaints:
            print("\nℹ️ No complaints found in database.")
            return
        
        print(f"\n📋 Sample Complaints (showing first 5 of {len(complaints)}):")
        print("=" * 50)
        
        for i, complaint in enumerate(complaints[:5]):
            print(f"\nComplaint {i+1}:")
            print(f"  ID: {complaint.id}")
            print(f"  Order ID: {complaint.order_id}")
            print(f"  Name: {complaint.name}")
            print(f"  Category: {complaint.complaint_category}")
            print(f"  Status: {complaint.processed.value}")
            print(f"  Importance: {complaint.importance_level.value if complaint.importance_level else 'Unknown'}")
            if complaint.processed_at:
                print(f"  Processed at: {complaint.processed_at}")
            if complaint.root_cause:
                print(f"  Root Cause: {complaint.root_cause[:100]}...")
            print("-" * 30)
        
        # Ask if user wants to search for a specific complaint
        try:
            search_choice = input("\nWould you like to search for a specific complaint by COMP ID or ORDER ID? (y/n): ").lower().strip()
            if search_choice in ['y', 'yes']:
                search_id = input("Enter COMP ID (e.g., COMP-000001) or ORDER ID: ").strip()
                found = None
                for c in complaints:
                    if c.id.lower() == search_id.lower() or (c.order_id and c.order_id.lower() == search_id.lower()):
                        found = c
                        break
                if found:
                    print("\n🔎 Complaint Found:")
                    print("=" * 50)
                    print(f"ID: {found.id}")
                    print(f"Order ID: {found.order_id}")
                    print(f"Name: {found.name}")
                    print(f"Email: {found.email}")
                    print(f"Contact Number: {found.contact_number}")
                    print(f"Product: {found.product_name}")
                    print(f"Purchase Date: {found.purchase_date}")
                    print(f"Category: {found.complaint_category}")
                    print(f"Description: {found.description}")
                    print(f"Photo Proof Link: {found.photo_proof_link}")
                    print(f"Importance: {found.importance_level.value if found.importance_level else 'Unknown'}")
                    print(f"Received At: {found.received_at}")
                    print(f"Status: {found.processed.value}")
                    print(f"Processed At: {found.processed_at}")
                    print(f"Root Cause: {found.root_cause}")
                    print(f"Suggested Solution: {found.suggested_solution}")
                    print("=" * 50)
                else:
                    print("❌ Complaint not found with that COMP ID or ORDER ID.")
        except KeyboardInterrupt:
            print("\nSearch cancelled.")
        except Exception as e:
            print(f"❌ Error during search: {e}")

    def show_welcome_message(self):
        """Show the welcome message"""
        print("🚀 Complaint Processing System")
        print("=" * 50)
        print("Welcome to the intelligent complaint analysis system!")
        print("This system will help you process and analyze customer complaints efficiently.")

    def show_goodbye_message(self):
        """Show the goodbye message"""
        print("\n👋 Thank you for using the Complaint Processing System!")

    def show_error_message(self, error):
        """Show error message"""
        print(f"❌ Error: {error}")

    def show_success_message(self, message):
        """Show success message"""
        print(f"✅ {message}")

    def show_info_message(self, message):
        """Show info message"""
        print(f"ℹ️ {message}")

    def get_user_choice(self, min_choice, max_choice):
        """Get user choice with validation"""
        try:
            choice = input(f"\nEnter your choice ({min_choice}-{max_choice}): ").strip()
            if choice.isdigit() and min_choice <= int(choice) <= max_choice:
                return choice
            else:
                print(f"❌ Invalid choice. Please enter a number between {min_choice}-{max_choice}.")
                return None
        except KeyboardInterrupt:
            print("\n\n👋 Goodbye!")
            return "exit"
        except Exception as e:
            print(f"❌ Error reading input: {e}")
            return None 