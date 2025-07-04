# 🚀 Complaints Email Response Automation

[![Python](https://img.shields.io/badge/Python-3.6+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

An intelligent email automation system that analyzes and generates appropriate responses to customer complaints, streamlining customer service operations.

---

## ✨ Features

- **Smart Complaint Analysis**: Automatically categorizes and analyzes incoming complaint emails using AI
- **Intelligent Response Generation**: Creates contextually appropriate responses based on complaint type
- **Google Sheets Integration**: Directly fetches complaints from Google Sheets
- **Database Integration**: Stores and manages complaint data efficiently (with duplicate prevention and sequential IDs)
- **Export Capabilities**: Generates detailed reports and analytics, export to CSV
- **Interactive Data Visualization**: Generate summary and dashboard charts (matplotlib, seaborn)
- **Sample & Search**: View sample complaints and search by COMP ID or ORDER ID
- **Modular Codebase**: Clean separation of UI, processing, and visualization logic
- **Safety Features**: Double confirmation for destructive actions, dangerous options at the bottom of the menu
- **Efficient Processing**: Only new/unprocessed/failed complaints are analyzed (no duplicate API calls)
- **Advanced Logging**: Rotating log files with automatic cleanup and management
- **Automatic Folder Creation**: Creates necessary folders for exports, charts, and logs
- **Professional File Organization**: Organized folder structure for better management

---

## 📸 Screenshots

### Main Menu

```
🚀 Complaint Processing System - Main Menu
==================================================
1. Load NEW complaints only
2. Process UNPROCESSED complaints only
3. Generate visualizations 📈
4. View database summary 📊
5. View sample complaints
6. Export complaints to CSV
7. Process PENDING & FAILED complaints 🔄
8. Mark ALL as unprocessed (reset status) ⚠️
9. Load and process ALL complaints (⚠️ full refresh)
10. Manage logs 📝
11. Exit
--------------------------------------------------
```

### Enhanced Database Summary

```
📊 Current Complaint Summary:
========================================
• Total: 26
• Processed: 26
• Pending: 0
• Failed: 0
• Success Rate: 100.0%
• Most common category: "Packaging Issue"
• Most common importance level: Medium
• Avg. processing time: 6.2 hours
========================================
[Optional] Would you like to view this as a chart? (y/n): y
📈 Chart saved as complaint_summary_20250619_201800.png
```

### Sample & Search

```
📋 Sample Complaints (showing first 5 of 26):
...
Would you like to search for a specific complaint by COMP ID or ORDER ID? (y/n): y
Enter COMP ID (e.g., COMP-000001) or ORDER ID: COMP-000005

✅ Complaint Found:
ID: COMP-000005
Order ID: ORD767658
Name: Kavitha Raj
...
```

### Log Management

```
📝 Log Management
========================================
📄 Current log file: complaint_analysis.log
   Size: 2.45 MB
   Last modified: 2025-01-15 14:30:22

📋 Last 5 log entries:
------------------------------
   2025-01-15 14:30:22 - __main__ - INFO - Application started
   2025-01-15 14:30:22 - __main__ - INFO - Log file: logs/complaint_analysis.log
   2025-01-15 14:30:22 - __main__ - INFO - ==================================================
   2025-01-15 14:30:22 - database - INFO - Database initialized successfully
   2025-01-15 14:30:22 - complaint_processor - INFO - Processing 5 pending complaints

Options:
1. View full current log
2. Clean up old timestamp-based logs
3. Back to main menu
```

---

## 📁 Project Structure

```
Complaints E-mail Response Automation/
├── 📁 config/                     # Configuration files
│   ├── .env                       # Environment variables (API keys)
│   └── credentials.json           # Google Sheets API credentials
├── 📁 data/                       # Database files
│   └── complaints.db              # SQLite database
├── 📁 logs/                       # Log files (auto-created)
│   ├── complaint_analysis.log     # Current log file
│   ├── complaint_analysis.log.1   # Backup (if > 5MB)
│   ├── complaint_analysis.log.2   # Backup (if > 5MB)
│   └── complaint_analysis.log.3   # Backup (if > 5MB)
├── 📁 exports/                    # CSV export files (auto-created)
│   └── complaints_export_2025-01-15_143022.csv
├── 📁 charts/                     # Chart images (auto-created)
│   ├── complaint_dashboard_2025-01-15_143022.png
│   └── complaint_summary_2025-01-15_143022.png
├── main.py                        # Main application with interactive menu
├── ai_analyzer.py                 # AI-powered complaint analysis
├── database.py                    # Database operations and models
├── export_handler.py              # Export functionality
├── complain_extractor.py          # Google Sheets data extraction
├── visualization_manager.py       # Data visualization and charting
├── complaint_processor.py         # Complaint processing logic
├── ui_manager.py                  # User interface and menu logic
├── requirements.txt               # Project dependencies
├── ComplaintAutomation.spec       # PyInstaller configuration
└── README.md                      # Project documentation
```

---

## 🆕 Recent Improvements

- **Modularized codebase** for maintainability and extensibility
- **Interactive, professional data visualizations** (matplotlib, seaborn)
- **Enhanced summary and search features**
- **Improved safety**: dangerous options at the bottom, double confirmation
- **Efficient, cost-effective AI processing** (no duplicate work)
- **Advanced logging system** with rotation and automatic cleanup
- **Automatic folder creation** for exports, charts, and logs
- **Professional file organization** with dedicated folders
- **Log management interface** with cleanup tools
- **Better error handling** and user feedback
- **Improved .exe compatibility** with proper file path handling

---

## 🛠️ Installation

1. **Clone the repository:**

   ```bash
   git clone <your-repository-url>
   cd Complaints-E-mail-Response-Automation
   ```

2. **Install required dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

---

## ⚙️ Configuration

1. **Create the config folder structure:**

   ```bash
   mkdir config data logs exports charts
   ```

2. **Create a `.env` file** in the `config` folder:

   ```env
   OPENAI_API_KEY=your_openai_api_key_here
   ```

3. **Place your Google Sheets API credentials file** (`credentials.json`) in the `config` folder

---

## 🚀 Usage

### Running the Application

```bash
python main.py
```

You'll be presented with a comprehensive menu and interactive prompts for statistics, charting, and complaint search.

### Building Executable

```bash
python -m PyInstaller ComplaintAutomation.spec
```

The executable will be created in the `dist` folder with all necessary configuration files included.

### Key Features

- **Smart Processing**: Only processes new/unprocessed complaints to avoid duplicate API calls
- **Automatic Organization**: Creates folders for exports, charts, and logs automatically
- **Log Management**: Built-in tools to view and clean up log files
- **Data Visualization**: Interactive charts and summaries
- **Export Capabilities**: CSV exports with timestamp-based naming
- **Search Functionality**: Find complaints by ID or order number

---

## 📊 Logging System

The application features an advanced logging system:

- **Single rotating log file** instead of multiple timestamp-based files
- **Automatic rotation** when file reaches 5MB
- **Backup management** (keeps 3 backup files maximum)
- **Log management interface** (Menu Option 10)
- **Automatic cleanup** of old timestamp-based logs on startup
- **Clear startup/shutdown markers** for easy debugging

---

## 🔧 Troubleshooting

### Common Issues

1. **API Key Not Found**: Ensure your `.env` file is in the `config` folder and contains `OPENAI_API_KEY=your_key`
2. **Missing Credentials**: Place `credentials.json` in the `config` folder
3. **Permission Errors**: Ensure the application has write permissions for creating folders
4. **Log File Issues**: Use the log management interface (Option 10) to view and clean up logs

### File Locations

- **Configuration**: `config/.env` and `config/credentials.json`
- **Database**: `data/complaints.db`
- **Logs**: `logs/complaint_analysis.log`
- **Exports**: `exports/` folder (auto-created)
- **Charts**: `charts/` folder (auto-created)

---

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

---

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

---

## 💬 Support

For support and queries, please open an issue in the repository.

---

_Made with ❤️ by [Yew Zhi Hao]_
