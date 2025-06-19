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
        """Show current database statistics"""
        stats = db.get_database_stats()
        
        print("\n📊 Current Database Statistics:")
        print("=" * 30)
        print(f"Total complaints: {stats['total']}")
        print(f"Pending: {stats['pending']}")
        print(f"Successfully processed: {stats['successful']}")
        print(f"Failed: {stats['failed']}")
        print(f"Processing success rate: {stats['processed_percentage']}%")

    def show_sample_complaints(self, db):
        """Show sample complaints from the database"""
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