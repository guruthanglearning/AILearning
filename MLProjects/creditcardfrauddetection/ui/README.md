# Credit Card Fraud Detection System - UI

This directory contains the Streamlit-based user interface for the Credit Card Fraud Detection System. The UI provides a comprehensive dashboard for fraud analysts and system administrators to monitor, analyze, and manage credit card transactions and fraud patterns.

## Features

### 1. Dashboard
- Real-time fraud metrics and KPIs
- Recent transaction activity with fraud status
- Fraud rate trend visualization
- System health overview

### 2. Transaction Analysis
- Real-time transaction analysis
- Sample transaction generation for testing
- Historical transaction lookup
- Detailed transaction visualization and explanation
- Analyst feedback mechanism

### 3. Fraud Patterns (Enhanced)
- **Enhanced UI with search and filtering capabilities**
- **CRUD operations**: Create, Read, Update, Delete fraud patterns
- **Advanced search**: Filter by name, description, or fraud type
- **Pattern management**: Add new patterns with JSON validation
- **Detailed view**: Popup modals with complete pattern information
- **Edit functionality**: Pre-filled forms for pattern updates
- **Delete confirmation**: Safety dialogs before pattern removal
- **Real-time data**: Live integration with backend API (1,000+ patterns)
- **Professional UI**: Modern design with responsive layout

### 4. System Health & Monitoring
- System status monitoring
- Performance metrics visualization
- Model performance tracking
- Resource utilization monitoring
- System logs with filtering
- Alert configuration

## Directory Structure

```
ui/
├── app.py                 # Main application entry point
├── api_client.py          # API client for backend communication
├── config.py              # Configuration settings
├── test_ui_functionality.py  # UI testing script
└── pages/                 # Multi-page application components
    ├── dashboard.py       # Dashboard page
    ├── transaction_analysis.py  # Transaction analysis page
    ├── fraud_patterns.py  # Enhanced fraud pattern management page
    └── system_health.py   # System health monitoring page
```

## Quick Start

### 1. Launch the System
```powershell
# From project root directory
.\launch_system_root.ps1
```
This will start both the API server (port 8000) and Streamlit UI (port 8501) in separate PowerShell windows.

### 2. Access the UI
Open your browser and navigate to: `http://localhost:8501`

### 3. Test Fraud Patterns
1. Click "Fraud Patterns" in the sidebar
2. Use search and filter features
3. Test CRUD operations (Add, Edit, Delete patterns)
4. View detailed pattern information

## Requirements

- Python 3.8+
- Streamlit 1.25.0+
- Pandas
- NumPy
- Plotly
- Requests

All required packages are listed in the project's main `requirements.txt` file.

## Setup and Running

1. Install the required dependencies:
   ```bash
   # From the project root directory
   pip install -r requirements.txt
   
   # If streamlit is not included in requirements.txt, install it separately
   pip install streamlit pandas numpy plotly requests
   ```

2. Set up environment variables (optional):
   - Create a `.env` file in the project root with:
     ```
     API_URL=http://localhost:8000  # Replace with your API URL
     API_KEY=your_api_key           # Replace with your API key
     ```

3. Run the Streamlit application:
   ```bash
   # From the project root directory
   cd creditcardfrauddetection
   streamlit run ui/app.py
   
   # Or using Python module
   python -m streamlit run ui/app.py
   ```

4. Access the UI in your web browser at `http://localhost:8501`

## API Integration

The UI communicates with the backend API for:
- Fraud detection analysis
- Transaction history retrieval
- Fraud pattern management
- System metrics collection

The `api_client.py` file handles all API communication, making it easy to modify or extend the integration as needed.

## Customization

- Color schemes and styling can be modified in the custom CSS section of `app.py`
- API endpoints and authentication can be configured in `config.py`
- Additional pages can be added to the `pages/` directory following the Streamlit multi-page app structure

## Development

To add new features or modify existing ones:

1. For page-specific changes, edit the corresponding file in the `pages/` directory
2. For application-wide changes, modify `app.py`
3. For API integration changes, update `api_client.py`

## Testing

### Automated Testing
Run the UI functionality test script:
```powershell
cd ui
python test_ui_functionality.py
```

This will verify:
- API connectivity and health status
- Streamlit UI accessibility
- Fraud patterns endpoint functionality
- System status and data availability

### Manual Testing
1. **Dashboard**: Verify metrics display and visualizations
2. **Transaction Analysis**: Test transaction processing and feedback
3. **Fraud Patterns**: Test all CRUD operations and filtering
4. **System Health**: Check monitoring and metrics display

### Testing Fraud Patterns Features
1. **Search Functionality**: Use the search box to filter patterns by name, description, or fraud type
2. **Filter by Type**: Use the dropdown to filter patterns by specific fraud types
3. **Add New Pattern**: Click "Add New Pattern" and fill in the form with JSON validation
4. **View Details**: Click the "👁️ View" button to see complete pattern information
5. **Edit Pattern**: Click "✏️ Edit" to modify existing patterns
6. **Delete Pattern**: Click "🗑️ Delete" and confirm the deletion

## Troubleshooting

### Common Issues

#### Module Import Errors
If you encounter syntax errors with module imports, ensure:
- File names don't start with numbers
- Import paths are correct
- All required modules are installed

#### API Connection Issues
If the UI cannot connect to the API:
1. Verify the API server is running on the expected port
2. Check the API_URL configuration
3. Ensure the API_KEY is correct
4. Wait 30-60 seconds for services to fully initialize

#### Streamlit Issues
- **Port already in use**: Kill existing Streamlit processes or use a different port
- **Module not found**: Ensure all dependencies are installed in the correct environment
- **Performance issues**: Clear browser cache and refresh the page

### Service Management
- **Start services**: Run `launch_system_root.ps1` from project root
- **Stop services**: Close the PowerShell windows opened by the launch script
- **Check status**: Use `netstat -ano | findstr :8000` and `netstat -ano | findstr :8501`

## Architecture

The UI follows a modular architecture:
- **app.py**: Main application with navigation and configuration
- **pages/**: Individual page components for different features
- **api_client.py**: Centralized API communication layer
- **config.py**: Configuration management

Each page is self-contained and can be developed/tested independently.

## Contributing

When adding new features:
1. Create new page modules in the `pages/` directory
2. Update the navigation in `app.py`
3. Add API methods to `api_client.py` if needed
4. Update this README with new features and usage instructions

## Recent Enhancements

### Fraud Patterns UI (July 2025)
- Enhanced search and filtering capabilities
- Complete CRUD operations with API integration
- Professional UI design with responsive layout
- Real-time data integration (1,000+ patterns)
- Advanced pattern management features
- Comprehensive error handling and validation
