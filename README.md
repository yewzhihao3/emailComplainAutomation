# 📧 Complaints Email Response Automation

[![Python](https://img.shields.io/badge/Python-3.6%2B-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

An intelligent email automation system that analyzes and generates appropriate responses to customer complaints, streamlining customer service operations.

## 🚀 Features

- **Smart Complaint Analysis**: Automatically categorizes and analyzes incoming complaint emails
- **Intelligent Response Generation**: Creates contextually appropriate responses based on complaint type
- **Database Integration**: Stores and manages complaint data efficiently
- **Export Capabilities**: Generates detailed reports and analytics
- **Mock Data Support**: Includes testing capabilities with mock data

## 📋 Prerequisites

- Python 3.6 or higher
- Required Python packages (installed via requirements.txt)

## 🛠️ Installation

1. Clone the repository:

   ```bash
   git clone <your-repository-url>
   cd Complaints-Email-Response-Automation
   ```

2. Install required dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## 🔧 Configuration

1. Create a `.env` file in the root directory
2. Add your API key:
   ```env
   API_KEY=your_api_key_here
   ```

## 💻 Usage

1. Run the main application:

   ```bash
   python main.py
   ```

   This will:

   - Load mock data from `mock_data.py` into the database
   - Start the complaint analysis system
   - Process complaints every hour
   - Generate reports every 6 hours

2. To analyze specific complaints:

   ```bash
   python ai_analyzer.py
   ```

3. To export processed complaints:
   ```bash
   python export_handler.py
   ```
   This will generate a CSV file (e.g., `complaints_export_2025-05-25_230815.csv`) containing the analyzed complaints data.

## 📁 Project Structure

```
├── main.py              # Main application entry point
├── ai_analyzer.py       # AI-powered complaint analysis
├── database.py         # Database operations and models
├── export_handler.py   # Export functionality
├── mock_data.py        # Test data generation
└── requirements.txt    # Project dependencies
```

## 📊 Data Handling

The system uses two types of data:

1. **Mock Data (`mock_data.py`)**:

   - Used for testing and development
   - Automatically loaded when you run `main.py`
   - Contains predefined complaint scenarios

2. **Exported Data (CSV files)**:
   - Generated from processed complaints in the database
   - Used for reporting and analysis
   - Example format: `complaints_export_2025-05-25_230815.csv`

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 📞 Support

For support and queries, please open an issue in the repository.

---

Made with ❤️ by [Your Name/Organization]
