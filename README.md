# TTN Data Processing Web App

A Streamlit web application that provides online tools for processing TTN IoT sensor data and removing duplicates from CSV files.

## Features

- **TTN Data Processing**: Upload TTN JSON data files and convert them to separate CSV files for each device
- **Duplicate Removal**: Upload CSV files to remove duplicate records based on customizable fields
- **Web Interface**: Easy-to-use web interface accessible to colleagues without Python installation

## Installation

1. Navigate to the application directory:
   ```bash
   cd TTN_data_process
   ```

2. Install dependencies using Poetry:
   ```bash
   poetry install
   ```

3. Activate the virtual environment:
   ```bash
   poetry shell
   ```

## Running the Application

1. Start the Streamlit app:
   ```bash
   streamlit run app.py
   ```

2. Open your web browser and go to the URL shown in the terminal (usually `http://localhost:8501`)

## Usage

### TTN Data Processing
1. Select "TTN Data Processing" from the sidebar
2. Upload your TTN JSON file (one JSON object per line)
3. The app will process the data and create separate CSV files for each device
4. Download individual CSV files or all files as a ZIP archive

### Duplicate Removal
1. Select "Duplicate Removal" from the sidebar
2. Upload one or more CSV files
3. Configure the duplicate detection fields (default: f_cnt, received_at)
4. Click "Remove Duplicates" to process the files
5. Download the deduplicated files

## Technical Details

- Built with Streamlit for easy web access
- Processes TTN JSON format (one JSON object per line)
- Supports multiple CSV file uploads for duplicate removal
- Provides download options for processed files

