#!/usr/bin/env python3
"""
TTN Data Processing Web App

A Streamlit web application that provides online tools for processing TTN IoT sensor data
and removing duplicates from CSV files.
"""

import streamlit as st
import json
import csv
import os
import tempfile
import shutil
from collections import defaultdict
from datetime import datetime
import io

# Set page configuration
st.set_page_config(
    page_title="TTN Data Processing",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .section-header {
        font-size: 1.5rem;
        color: #2e86ab;
        margin-top: 2rem;
        margin-bottom: 1rem;
    }
    .success-box {
        background-color: #d4edda;
        border: 1px solid #c3e6cb;
        border-radius: 5px;
        padding: 15px;
        margin: 10px 0;
    }
    .info-box {
        background-color: #d1ecf1;
        border: 1px solid #bee5eb;
        border-radius: 5px;
        padding: 15px;
        margin: 10px 0;
    }
</style>
""", unsafe_allow_html=True)


def parse_json_data(json_content):
    """
    Parse JSON data content and extract data by device type.
    
    Args:
        json_content (str): JSON content as string
        
    Returns:
        dict: Dictionary with device types as keys and lists of data records as values
    """
    device_data = defaultdict(list)
    
    lines = json_content.strip().split('\n')
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
            
        try:
            data = json.loads(line)
            result = data.get('result', {})
            
            # Extract device information
            end_device_ids = result.get('end_device_ids', {})
            device_id = end_device_ids.get('device_id', 'unknown')
            
            # Extract timestamp
            received_at = result.get('received_at', '')
            
            # Extract sensor data from uplink message
            uplink_message = result.get('uplink_message', {})
            decoded_payload = uplink_message.get('decoded_payload', {})
            
            # Create data record with common fields
            record = {
                'device_id': device_id,
                'received_at': received_at,
                'f_port': uplink_message.get('f_port', ''),
                'f_cnt': uplink_message.get('f_cnt', '')
            }
            
            # Add all sensor data from decoded payload
            record.update(decoded_payload)
            
            # Add to device-specific data
            device_data[device_id].append(record)
            
        except json.JSONDecodeError as e:
            st.warning(f"Could not parse line: {line[:100]}... Error: {e}")
            continue
    
    return device_data


def create_csv_files(device_data):
    """
    Create separate CSV files for each device type.
    
    Args:
        device_data (dict): Dictionary with device data
        
    Returns:
        dict: Dictionary with device IDs as keys and CSV content as values
    """
    csv_files = {}
    
    for device_id, records in device_data.items():
        if not records:
            continue
            
        # Get all unique field names from all records
        fieldnames = set()
        for record in records:
            fieldnames.update(record.keys())
        
        # Convert to list and sort for consistent order
        fieldnames = sorted(list(fieldnames))
        
        # Create CSV content in memory
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=fieldnames)
        writer.writeheader()
        
        for record in records:
            # Ensure all fields are present in each record
            full_record = {field: record.get(field, '') for field in fieldnames}
            writer.writerow(full_record)
        
        csv_files[device_id] = output.getvalue()
        output.close()
    
    return csv_files


def remove_duplicates_from_csv(csv_content, unique_fields=None):
    """
    Remove duplicate records from CSV content.
    
    Args:
        csv_content (str): CSV content as string
        unique_fields (list): List of field names to use for duplicate detection
        
    Returns:
        tuple: (deduplicated_csv_content, original_count, unique_count, duplicates_removed)
    """
    if unique_fields is None:
        unique_fields = ['f_cnt', 'received_at']
    
    # Read CSV content
    reader = csv.DictReader(io.StringIO(csv_content))
    fieldnames = reader.fieldnames
    records = list(reader)
    
    original_count = len(records)
    
    # Remove duplicates
    seen = set()
    unique_records = []
    duplicates_removed = 0
    
    for record in records:
        # Create a unique key from the specified fields
        key_parts = []
        for field in unique_fields:
            if field in record:
                key_parts.append(str(record[field]))
            else:
                key_parts.append('')
        
        key = '|'.join(key_parts)
        
        if key not in seen:
            seen.add(key)
            unique_records.append(record)
        else:
            duplicates_removed += 1
    
    unique_count = len(unique_records)
    
    # Create deduplicated CSV content
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(unique_records)
    
    deduplicated_content = output.getvalue()
    output.close()
    
    return deduplicated_content, original_count, unique_count, duplicates_removed


def main():
    """Main Streamlit application."""
    
    # Header
    st.markdown('<div class="main-header">📊 TTN Data Processing Tools</div>', unsafe_allow_html=True)
    
    # Sidebar
    st.sidebar.title("Navigation")
    app_mode = st.sidebar.selectbox(
        "Choose a tool:",
        ["TTN Data Processing", "Duplicate Removal", "About"]
    )
    
    if app_mode == "TTN Data Processing":
        show_data_processing()
    elif app_mode == "Duplicate Removal":
        show_duplicate_removal()
    else:
        show_about()


def show_data_processing():
    """Show the TTN data processing interface."""
    
    st.markdown('<div class="section-header">📥 TTN Data Processing</div>', unsafe_allow_html=True)
    
    st.markdown("""
    Upload your TTN JSON data file to process it into separate CSV files for each device.
    The JSON file should contain one JSON object per line from TTN's data export.
    """)
    
    # File upload
    uploaded_file = st.file_uploader(
        "Upload TTN JSON file",
        type=['json', 'txt'],
        help="Upload a JSON file containing TTN sensor data (one JSON object per line)"
    )
    
    if uploaded_file is not None:
        # Read the uploaded file
        json_content = uploaded_file.read().decode('utf-8')
        
        # Process the data
        with st.spinner('Processing TTN data...'):
            device_data = parse_json_data(json_content)
            csv_files = create_csv_files(device_data)
        
        # Display results
        st.markdown('<div class="success-box">', unsafe_allow_html=True)
        st.success(f"✅ Successfully processed data for {len(device_data)} devices!")
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Show summary
        st.subheader("Processing Summary")
        
        # Display summary as markdown table instead of using st.table()
        summary_markdown = "| Device ID | Records | CSV File |\n"
        summary_markdown += "|-----------|---------|----------|\n"
        
        for device_id, records in device_data.items():
            summary_markdown += f"| {device_id} | {len(records)} | {device_id}_data.csv |\n"
        
        st.markdown(summary_markdown)
        
        # Download buttons for each CSV file
        st.subheader("Download Processed CSV Files")
        
        cols = st.columns(3)
        for idx, (device_id, csv_content) in enumerate(csv_files.items()):
            col_idx = idx % 3
            with cols[col_idx]:
                filename = f"{device_id}_data.csv"
                st.download_button(
                    label=f"Download {filename}",
                    data=csv_content,
                    file_name=filename,
                    mime="text/csv",
                    key=f"download_{device_id}"
                )
        
        # Download all files as ZIP
        if len(csv_files) > 1:
            st.subheader("Download All Files")
            
            # Create a temporary directory and zip file
            with tempfile.TemporaryDirectory() as temp_dir:
                zip_path = os.path.join(temp_dir, "processed_data.zip")
                
                with st.spinner('Creating ZIP file...'):
                    # Write all CSV files to temp directory
                    for device_id, csv_content in csv_files.items():
                        file_path = os.path.join(temp_dir, f"{device_id}_data.csv")
                        with open(file_path, 'w') as f:
                            f.write(csv_content)
                    
                    # Create ZIP file
                    shutil.make_archive(zip_path.replace('.zip', ''), 'zip', temp_dir)
                    
                    # Read ZIP file for download
                    with open(zip_path, 'rb') as f:
                        zip_data = f.read()
                
                st.download_button(
                    label="📦 Download All Files as ZIP",
                    data=zip_data,
                    file_name="processed_data.zip",
                    mime="application/zip",
                    key="download_all"
                )


def show_duplicate_removal():
    """Show the duplicate removal interface."""
    
    st.markdown('<div class="section-header">🔍 Duplicate Removal Tool</div>', unsafe_allow_html=True)
    
    st.markdown("""
    Upload CSV files to remove duplicate records. The tool will identify duplicates based on
    unique identifiers like `f_cnt` and `received_at` fields.
    """)
    
    # File upload
    uploaded_files = st.file_uploader(
        "Upload CSV files",
        type=['csv'],
        accept_multiple_files=True,
        help="Upload one or more CSV files to remove duplicates from"
    )
    
    if uploaded_files:
        # Configuration
        st.subheader("Configuration")
        
        col1, col2 = st.columns(2)
        
        with col1:
            unique_fields = st.multiselect(
                "Fields to use for duplicate detection:",
                options=['f_cnt', 'received_at', 'device_id', 'f_port'],
                default=['f_cnt', 'received_at'],
                help="Select the fields that uniquely identify a record"
            )
        
        with col2:
            create_backup = st.checkbox(
                "Create backup of original files",
                value=True,
                help="Download original files alongside deduplicated versions"
            )
        
        if not unique_fields:
            st.warning("Please select at least one field for duplicate detection.")
            return
        
        # Process files
        if st.button("Remove Duplicates", type="primary"):
            total_original = 0
            total_unique = 0
            total_duplicates = 0
            processed_files = {}
            
            with st.spinner('Removing duplicates...'):
                for uploaded_file in uploaded_files:
                    # Read CSV content
                    csv_content = uploaded_file.read().decode('utf-8')
                    
                    # Remove duplicates
                    deduplicated_content, original_count, unique_count, duplicates_removed = remove_duplicates_from_csv(
                        csv_content, unique_fields
                    )
                    
                    # Store results
                    processed_files[uploaded_file.name] = {
                        'original': csv_content,
                        'deduplicated': deduplicated_content,
                        'original_count': original_count,
                        'unique_count': unique_count,
                        'duplicates_removed': duplicates_removed
                    }
                    
                    # Update totals
                    total_original += original_count
                    total_unique += unique_count
                    total_duplicates += duplicates_removed
            
            # Display results
            st.markdown('<div class="success-box">', unsafe_allow_html=True)
            st.success(f"✅ Successfully processed {len(uploaded_files)} files!")
            st.markdown('</div>', unsafe_allow_html=True)
            
            # Show detailed results
            st.subheader("Processing Results")
            
            # Display results as markdown table instead of using st.table()
            results_markdown = "| File | Original Records | Unique Records | Duplicates Removed |\n"
            results_markdown += "|------|-----------------|---------------|-------------------|\n"
            
            for filename, data in processed_files.items():
                results_markdown += f"| {filename} | {data['original_count']} | {data['unique_count']} | {data['duplicates_removed']} |\n"
            
            st.markdown(results_markdown)
            
            # Summary
            st.subheader("Summary")
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Total Original Records", total_original)
            with col2:
                st.metric("Total Unique Records", total_unique)
            with col3:
                st.metric("Total Duplicates Removed", total_duplicates)
            
            # Download processed files
            st.subheader("Download Processed Files")
            
            for filename, data in processed_files.items():
                col1, col2 = st.columns([3, 1])
                
                with col1:
                    st.write(f"**{filename}**")
                    st.write(f"Original: {data['original_count']} records → Deduplicated: {data['unique_count']} records")
                
                with col2:
                    # Download deduplicated file
                    deduplicated_filename = f"deduplicated_{filename}"
                    st.download_button(
                        label="Download",
                        data=data['deduplicated'],
                        file_name=deduplicated_filename,
                        mime="text/csv",
                        key=f"dedup_{filename}"
                    )
                    
                    # Download original file (if backup requested)
                    if create_backup:
                        st.download_button(
                            label="Original",
                            data=data['original'],
                            file_name=filename,
                            mime="text/csv",
                            key=f"orig_{filename}"
                        )


def show_about():
    """Show the about page."""
    
    st.markdown('<div class="section-header">ℹ️ About</div>', unsafe_allow_html=True)
    
    st.markdown("""
    ## TTN Data Processing Web App
    
    This web application provides online tools for processing IoT sensor data from The Things Network (TTN).
    
    ### Features
    
    **📥 TTN Data Processing**
    - Upload TTN JSON data files (one JSON object per line)
    - Process data into separate CSV files for each device
    - Download individual CSV files or all files as ZIP
    
    **🔍 Duplicate Removal Tool**
    - Upload CSV files to remove duplicate records
    - Customizable duplicate detection fields
    - Download original and deduplicated files
    
    ### How to Use
    
    1. **TTN Data Processing**: Upload your TTN JSON export file to create separate CSV files for each device
    2. **Duplicate Removal**: Upload CSV files to remove duplicate records based on selected fields
    
    ### Technical Details
    
    - Built with Streamlit for easy web access
    - Processes TTN JSON format (one JSON object per line)
    - Supports multiple CSV file uploads for duplicate removal
    - Provides download options for processed files
    
    """)


if __name__ == "__main__":
    main()
