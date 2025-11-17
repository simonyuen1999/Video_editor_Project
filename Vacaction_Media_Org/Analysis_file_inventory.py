#!/usr/bin/env python3
"""
File Inventory Analysis Tool

This script reads multiple CSV file inventories and creates an HTML summary page
using MD5 checksums as unique identifiers to track files across different inventories.

Usage:
    python Analysis_file_inventory.py file1.csv file2.csv file3.csv file4.csv

Output:
    Creates an HTML file with analysis of file inventories including:
    - Summary table of CSV files
    - File comparison across inventories
    - Duplicate detection
    - Missing/new files analysis
"""

import csv
import sys
import os
import logging
from datetime import datetime
from pathlib import Path
import json

class FileInventoryAnalyzer:
    def __init__(self):
        self.inventories = {}
        self.all_files = {}  # checksum -> file info
        self.file_locations = {}  # checksum -> list of inventories containing this file
        self.setup_logging()
    
    def setup_logging(self):
        """Setup logging configuration for error tracking."""
        log_filename = f"analysis_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        
        # Create logger
        self.logger = logging.getLogger(f'FileInventoryAnalyzer_{id(self)}')
        self.logger.setLevel(logging.INFO)
        
        # Remove any existing handlers to avoid duplicates
        for handler in self.logger.handlers[:]:
            self.logger.removeHandler(handler)
        
        # Create file handler
        file_handler = logging.FileHandler(log_filename, encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)  # Log everything to file
        
        # Create formatter
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(formatter)
        
        # Add handler to logger
        self.logger.addHandler(file_handler)
        
        # Prevent propagation to root logger to avoid console duplication
        self.logger.propagate = False
        
        self.log_file = log_filename
        
        # Log session start
        self.logger.info("="*80)
        self.logger.info(f"File Inventory Analysis Session Started")
        self.logger.info(f"Log file: {log_filename}")
        self.logger.info("="*80)
        
    def load_csv_inventory(self, csv_path, inventory_name=None):
        """
        Load a CSV inventory file.
        
        Args:
            csv_path (str): Path to CSV file
            inventory_name (str): Optional name for the inventory
        
        Returns:
            dict: Loaded inventory data
        """
        if inventory_name is None:
            inventory_name = Path(csv_path).stem
        
        inventory_data = {
            'name': inventory_name,
            'path': csv_path,
            'files': {},
            'total_files': 0,
            'unique_files': 0,
            'load_time': datetime.now().isoformat(),
            'debug_stats': {
                'total_rows': 0,
                'skipped_invalid': 0,
                'skipped_empty_checksum': 0,
                'skipped_error_checksum': 0,
                'skipped_empty_filename': 0,
                'processed_files': 0,
                'duplicate_checksums': 0,
                'invalid_entries': []
            }
        }
        
        self.logger.info(f"Loading inventory: {csv_path} as '{inventory_name}'")
        
        try:
            with open(csv_path, 'r', encoding='utf-8') as csvfile:
                reader = csv.DictReader(csvfile)
                self.logger.info(f"CSV file opened successfully: {csv_path}")
                
                for row in reader:
                    checksum = row.get('checksum', '').strip()
                    filename = row.get('filename', '').strip()
                    modify_time = row.get('modify_time', '').strip()
                    relative_path = row.get('relative_path', '').strip()
                    
                    # Skip LRF files completely (as if they don't exist)
                    if filename.upper().endswith('.LRF'):
                        self.logger.debug(f"Skipped LRF file: {filename} in {relative_path}")
                        continue
                    
                    inventory_data['debug_stats']['total_rows'] += 1
                    
                    # Debug: Track invalid entries
                    skip_reason = None
                    
                    # Skip empty checksum
                    if not checksum:
                        inventory_data['debug_stats']['skipped_empty_checksum'] += 1
                        skip_reason = 'empty_checksum'
                        self.logger.warning(f"Empty checksum found - File: {filename}, Path: {relative_path}, Inventory: {inventory_name}")
                    # Skip ERROR checksum
                    elif checksum == 'ERROR':
                        inventory_data['debug_stats']['skipped_error_checksum'] += 1
                        skip_reason = 'error_checksum'
                        self.logger.error(f"ERROR checksum found - File: {filename}, Path: {relative_path}, Inventory: {inventory_name}")
                    # Skip empty filename
                    elif not filename:
                        inventory_data['debug_stats']['skipped_empty_filename'] += 1
                        skip_reason = 'empty_filename'
                        self.logger.warning(f"Empty filename found - Checksum: {checksum}, Path: {relative_path}, Inventory: {inventory_name}")
                    
                    # If there's a skip reason, record it and continue
                    if skip_reason:
                        inventory_data['debug_stats']['skipped_invalid'] += 1
                        if len(inventory_data['debug_stats']['invalid_entries']) < 20:  # Limit to first 20
                            inventory_data['debug_stats']['invalid_entries'].append({
                                'filename': filename or 'N/A',
                                'checksum': checksum or 'N/A',
                                'relative_path': relative_path or 'N/A',
                                'reason': skip_reason
                            })
                        self.logger.info(f"Skipped invalid entry: {skip_reason} - File: {filename or 'N/A'}, Inventory: {inventory_name}")
                        continue
                    
                    inventory_data['total_files'] += 1
                    inventory_data['debug_stats']['processed_files'] += 1
                    
                    # Store file info in inventory
                    file_info = {
                        'filename': filename,
                        'modify_time': modify_time,
                        'relative_path': relative_path,
                        'full_path': os.path.join(relative_path, filename) if relative_path else filename
                    }
                    
                    # Check if checksum already exists in this inventory
                    if checksum in inventory_data['files']:
                        inventory_data['debug_stats']['duplicate_checksums'] += 1
                        existing_file = inventory_data['files'][checksum]
                        self.logger.warning(f"Duplicate checksum found in {inventory_name}:")
                        self.logger.warning(f"  Existing: {existing_file['filename']} in {existing_file['relative_path']}")
                        self.logger.warning(f"  Duplicate: {filename} in {relative_path}")
                        self.logger.warning(f"  Checksum: {checksum}")
                    else:
                        inventory_data['files'][checksum] = file_info
                    
                    # Track in global collections
                    if checksum not in self.all_files:
                        self.all_files[checksum] = file_info.copy()
                        self.file_locations[checksum] = []
                    
                    self.file_locations[checksum].append(inventory_name)
                
                inventory_data['unique_files'] = len(inventory_data['files'])
                
                # Log summary statistics
                self.logger.info(f"Inventory loading completed for: {inventory_name}")
                self.logger.info(f"  Total rows processed: {inventory_data['debug_stats']['total_rows']}")
                self.logger.info(f"  Valid files loaded: {inventory_data['total_files']}")
                self.logger.info(f"  Unique files: {inventory_data['unique_files']}")
                self.logger.info(f"  Invalid entries skipped: {inventory_data['debug_stats']['skipped_invalid']}")
                self.logger.info(f"  Duplicate checksums: {inventory_data['debug_stats']['duplicate_checksums']}")
                
        except Exception as e:
            self.logger.error(f"Critical error loading {csv_path}: {e}")
            print(f"❌ Error loading {csv_path}: {e}")
            return None
        
        self.inventories[inventory_name] = inventory_data
        return inventory_data
    
    def analyze_inventories(self):
        """Analyze loaded inventories and generate statistics."""
        self.logger.info("Starting inventory analysis...")
        
        analysis = {
            'total_inventories': len(self.inventories),
            'total_unique_files': len(self.all_files),
            'duplicates': {},
            'unique_to_inventory': {},
            'common_files': {},
            'file_distribution': {}
        }
        
        self.logger.info(f"Analysis parameters: {len(self.inventories)} inventories, {len(self.all_files)} unique files")
        
        # Analyze file distribution
        for checksum, locations in self.file_locations.items():
            location_count = len(locations)
            
            if location_count not in analysis['file_distribution']:
                analysis['file_distribution'][location_count] = 0
            analysis['file_distribution'][location_count] += 1
            
            # Files present in multiple inventories (duplicates)
            if location_count > 1:
                analysis['duplicates'][checksum] = {
                    'file_info': self.all_files[checksum],
                    'locations': locations,
                    'count': location_count
                }
            
            # Files unique to single inventory
            elif location_count == 1:
                inventory_name = locations[0]
                if inventory_name not in analysis['unique_to_inventory']:
                    analysis['unique_to_inventory'][inventory_name] = []
                analysis['unique_to_inventory'][inventory_name].append({
                    'checksum': checksum,
                    'file_info': self.all_files[checksum]
                })
        
        # Find common files (present in all inventories)
        if len(self.inventories) > 1:
            for checksum, locations in self.file_locations.items():
                if len(locations) == len(self.inventories):
                    analysis['common_files'][checksum] = {
                        'file_info': self.all_files[checksum],
                        'locations': locations
                    }
        
        # Log analysis results
        self.logger.info("Analysis completed with the following results:")
        self.logger.info(f"  Total inventories: {analysis['total_inventories']}")
        self.logger.info(f"  Total unique files: {analysis['total_unique_files']}")
        self.logger.info(f"  Duplicate files: {len(analysis['duplicates'])}")
        self.logger.info(f"  Common files (in all inventories): {len(analysis['common_files'])}")
        
        for inventory_name, unique_files in analysis['unique_to_inventory'].items():
            self.logger.info(f"  Files unique to {inventory_name}: {len(unique_files)}")
        
        return analysis
    
    def generate_html_report(self, output_file='file_inventory_analysis.html'):
        """Generate HTML report from analysis."""
        self.logger.info(f"Generating HTML report: {output_file}")
        
        analysis = self.analyze_inventories()
        
        self.logger.info("Generating HTML template...")
        html_content = self._generate_html_template(analysis)
        
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            self.logger.info(f"HTML report successfully generated: {output_file}")
            self.logger.info(f"Report size: {len(html_content):,} characters")
            
        except Exception as e:
            self.logger.error(f"Failed to write HTML report: {e}")
            raise
        
        return output_file
    
    def _shorten_csv_name(self, csv_name):
        """Shorten CSV filename for table header."""
        # Remove extension and base directory
        name = os.path.basename(csv_name).replace('.csv', '')
        
        # Apply shortening rules
        shortcuts = {
            'SanDisk_Video': 'SD_Video',
            'SanDisk_Simon_media': 'SD_Simon',
            'SSD_Videos_Original_Inc_Simon_iPhone': 'SSD_Original',
            'SSD_2025HKTrip_Organized_from_Original': 'HK_Trip',
            'Videos_Original_Inc_Simon_iPhone': 'Original_Video',
            'Organized_from_Original': 'Organized'
        }
        
        # Check for exact matches first
        if name in shortcuts:
            return shortcuts[name]
        
        # Apply pattern-based shortening
        for pattern, short in shortcuts.items():
            if pattern in name:
                return short
        
        # Generic shortening - take first 10 characters
        return name[:10] + ('...' if len(name) > 10 else '')
    
    def _generate_files_comparison_table(self):
        """Generate the main files comparison table."""
        if not self.all_files:
            return ""
        
        # Get ordered list of inventory names
        inventory_names = list(self.inventories.keys())
        
        # Create table headers
        headers = ['#', 'MD5 Checksum'] + [self._shorten_csv_name(name) for name in inventory_names]
        
        # Generate all table rows
        table_rows = ""
        counter = 1
        initial_display_limit = 200
        
        for checksum, file_info in self.all_files.items():
            # Create row data
            row_data = {
                'counter': counter,
                'checksum': checksum,
                'files': {}
            }
            
            # Check each inventory for this file
            for inv_name in inventory_names:
                if checksum in self.inventories[inv_name]['files']:
                    inv_file = self.inventories[inv_name]['files'][checksum]
                    row_data['files'][inv_name] = {
                        'filename': inv_file['filename'],
                        'modify_time': inv_file['modify_time'],
                        'relative_path': inv_file['relative_path'],
                        'full_path': inv_file['full_path']
                    }
                else:
                    row_data['files'][inv_name] = None
            
            # Generate table row HTML
            cells = [
                f"<td>{counter}</td>",
                f"<td><code title='{checksum}'>{checksum[:12]}...</code></td>"
            ]
            
            for inv_name in inventory_names:
                if row_data['files'][inv_name]:
                    filename = row_data['files'][inv_name]['filename']
                    cells.append(f"<td>{filename}</td>")
                else:
                    cells.append("<td class='missing'>-</td>")
            
            # Create onclick handler with detailed info
            detail_data = {
                'counter': counter,
                'checksum': checksum,
                'files': row_data['files']
            }
            
            # Use data attributes instead of onclick with JSON
            onclick_data = json.dumps(detail_data).replace("'", "&#39;").replace('"', '&quot;')
            
            # Add display class for initial limit
            display_class = "" if counter <= initial_display_limit else " style='display: none;'"
            
            table_rows += f"""
            <tr class="clickable-row all-files-row" data-file-info='{onclick_data}'{display_class}>
                {''.join(cells)}
            </tr>
            """
            
            counter += 1
        
        # Generate complete table HTML
        header_cells = ''.join([f"<th>{header}</th>" for header in headers])
        
        # Create show all files button if there are more files than initial display
        show_all_button = ""
        if len(self.all_files) > initial_display_limit:
            remaining_count = len(self.all_files) - initial_display_limit
            show_all_button = f"""
                <div class="show-more-container" style="text-align: center; margin: 10px 0;">
                    <button onclick="toggleAllFiles()" id="showAllBtn" class="btn-secondary">
                        Show All Files (+{remaining_count:,} more)
                    </button>
                </div>
            """

        return f"""
        <div class="section">
            <h2>📄 File Comparison Table</h2>
            <div class="section-content">
                <p>Click on any row to see detailed file information. Total files: <strong>{len(self.all_files):,}</strong></p>
                <p><small>Showing first {min(initial_display_limit, len(self.all_files))} files by default. Click "Show All Files" for scrollable view.</small></p>
                <div id="tableContainer" class="table-container">
                    <table id="filesTable" class="files-table">
                        <thead>
                            <tr>{header_cells}</tr>
                        </thead>
                        <tbody id="allFilesRows">
                            {table_rows}
                        </tbody>
                    </table>
                </div>
                {show_all_button}
            </div>
        </div>
        """
    
    def _generate_html_template(self, analysis):
        """Generate the HTML template with analysis data."""
        
        # Generate inventory summary table
        inventory_table_rows = ""
        for name, data in self.inventories.items():
            inventory_table_rows += f"""
            <tr>
                <td>{name}</td>
                <td>{os.path.basename(data['path'])}</td>
                <td>{data['debug_stats']['total_rows']:,}</td>
                <td>{data['total_files']:,}</td>
                <td>{data['unique_files']:,}</td>
            </tr>
            """
        
        # Generate debug summary table
        debug_table_rows = ""
        for name, data in self.inventories.items():
            debug_stats = data['debug_stats']
            debug_table_rows += f"""
            <tr>
                <td>{name}</td>
                <td>{debug_stats['total_rows']:,}</td>
                <td>{debug_stats['processed_files']:,}</td>
                <td>{debug_stats['skipped_invalid']:,}</td>
                <td>{debug_stats['skipped_empty_checksum']:,}</td>
                <td>{debug_stats['skipped_error_checksum']:,}</td>
                <td>{debug_stats['duplicate_checksums']:,}</td>
            </tr>
            """
        
        # Generate invalid entries details
        debug_details_rows = ""
        for name, data in self.inventories.items():
            for invalid_entry in data['debug_stats']['invalid_entries']:
                debug_details_rows += f"""
                <tr>
                    <td>{name}</td>
                    <td>{invalid_entry['filename']}</td>
                    <td><code>{invalid_entry['checksum'][:20]}{'...' if len(invalid_entry['checksum']) > 20 else ''}</code></td>
                    <td>{invalid_entry['relative_path']}</td>
                    <td><span class="reason-{invalid_entry['reason']}">{invalid_entry['reason'].replace('_', ' ').title()}</span></td>
                </tr>
                """
        
        # Generate duplicates table
        duplicates_rows = ""
        for checksum, dup_info in list(analysis['duplicates'].items())[:50]:  # Limit to first 50
            file_info = dup_info['file_info']
            locations_str = ", ".join(dup_info['locations'])
            duplicates_rows += f"""
            <tr>
                <td><code>{checksum[:16]}...</code></td>
                <td>{file_info['filename']}</td>
                <td>{file_info.get('relative_path', '')}</td>
                <td>{dup_info['count']}</td>
                <td><small>{locations_str}</small></td>
            </tr>
            """
        
        # Generate unique files sections
        unique_sections = ""
        for inventory_name, unique_files in analysis['unique_to_inventory'].items():
            unique_rows = ""
            for item in unique_files[:20]:  # Limit to first 20
                file_info = item['file_info']
                unique_rows += f"""
                <tr>
                    <td><code>{item['checksum'][:16]}...</code></td>
                    <td>{file_info['filename']}</td>
                    <td>{file_info.get('relative_path', '')}</td>
                    <td>{file_info.get('modify_time', '')}</td>
                </tr>
                """
            
            unique_sections += f"""
            <div class="section">
                <h3>📁 Files Unique to: {inventory_name}</h3>
                <p>Total unique files: <strong>{len(unique_files):,}</strong></p>
                <table>
                    <thead>
                        <tr>
                            <th>Checksum</th>
                            <th>Filename</th>
                            <th>Path</th>
                            <th>Modified</th>
                        </tr>
                    </thead>
                    <tbody>
                        {unique_rows}
                    </tbody>
                </table>
                {f'<p><small>Showing first 20 of {len(unique_files)} files...</small></p>' if len(unique_files) > 20 else ''}
            </div>
            """
        
        # Generate common files table
        common_rows = ""
        for checksum, common_info in list(analysis['common_files'].items())[:20]:
            file_info = common_info['file_info']
            common_rows += f"""
            <tr>
                <td><code>{checksum[:16]}...</code></td>
                <td>{file_info['filename']}</td>
                <td>{file_info.get('relative_path', '')}</td>
                <td>{file_info.get('modify_time', '')}</td>
            </tr>
            """
        
        html_template = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>File Inventory Analysis Report</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            line-height: 1.6;
            color: #333;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
        }}
        
        .container {{
            width: 100%;
            margin: 0;
            padding: 20px;
        }}
        
        .header {{
            background: white;
            padding: 30px;
            border-radius: 10px;
            box-shadow: 0 4px 20px rgba(0,0,0,0.1);
            margin-bottom: 30px;
            text-align: center;
        }}
        
        .header h1 {{
            color: #667eea;
            margin-bottom: 10px;
            font-size: 2.5em;
        }}
        
        .header .subtitle {{
            color: #666;
            font-size: 1.1em;
        }}
        
        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }}
        
        .stat-card {{
            background: white;
            padding: 20px;
            border-radius: 10px;
            box-shadow: 0 4px 15px rgba(0,0,0,0.1);
            text-align: center;
        }}
        
        .stat-value {{
            font-size: 2em;
            font-weight: bold;
            color: #667eea;
            margin-bottom: 5px;
        }}
        
        .stat-label {{
            color: #666;
            text-transform: uppercase;
            font-size: 0.9em;
            letter-spacing: 1px;
        }}
        
        .section {{
            background: white;
            margin-bottom: 30px;
            border-radius: 10px;
            box-shadow: 0 4px 15px rgba(0,0,0,0.1);
            overflow: hidden;
        }}
        
        .section h2, .section h3 {{
            background: linear-gradient(135deg, #667eea, #764ba2);
            color: white;
            padding: 20px;
            margin: 0;
        }}
        
        .collapsible-header {{
            background: linear-gradient(135deg, #667eea, #764ba2);
            color: white;
            padding: 20px;
            margin: 0;
            cursor: pointer;
            user-select: none;
            transition: background 0.3s ease;
        }}
        
        .collapsible-header:hover {{
            background: linear-gradient(135deg, #5a6fd8, #6a4190);
        }}
        
        .btn-secondary {{
            background-color: #6c757d;
            color: white;
            border: none;
            padding: 10px 20px;
            border-radius: 5px;
            cursor: pointer;
            font-size: 14px;
            transition: background-color 0.3s ease;
        }}
        
        .btn-secondary:hover {{
            background-color: #5a6268;
        }}
        
        /* Debug reason styling */
        .reason-empty_checksum {{ 
            background-color: #ffebee; 
            color: #c62828; 
            padding: 2px 6px; 
            border-radius: 3px; 
            font-size: 0.85em; 
        }}
        .reason-error_checksum {{ 
            background-color: #fce4ec; 
            color: #ad1457; 
            padding: 2px 6px; 
            border-radius: 3px; 
            font-size: 0.85em; 
        }}
        .reason-empty_filename {{ 
            background-color: #fff3e0; 
            color: #ef6c00; 
            padding: 2px 6px; 
            border-radius: 3px; 
            font-size: 0.85em; 
        }}

        
        .section-content {{
            padding: 20px;
        }}
        
        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 15px 0;
        }}
        
        th, td {{
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #ddd;
        }}
        
        th {{
            background: #f8f9fa;
            font-weight: bold;
            color: #333;
        }}
        
        tr:hover {{
            background: #f8f9fa;
        }}
        
        code {{
            background: #f1f3f4;
            padding: 2px 6px;
            border-radius: 4px;
            font-family: 'Monaco', 'Consolas', monospace;
            font-size: 0.9em;
        }}
        
        .chart-container {{
            height: 300px;
            margin: 20px 0;
        }}
        
        .timestamp {{
            text-align: center;
            color: #666;
            font-style: italic;
            margin-top: 30px;
        }}
        
        /* Files comparison table styles */
        .table-container {{
            border-radius: 5px;
            transition: all 0.3s ease;
        }}
        
        /* Scrollable state for table container */
        .table-container.scrollable {{
            max-height: 600px;
            overflow-y: auto;
            border: 1px solid #ddd;
        }}
        
        .files-table {{
            margin: 0;
            position: sticky;
        }}
        
        .files-table thead th {{
            position: sticky;
            top: 0;
            background: #667eea;
            color: white;
            z-index: 10;
        }}
        
        .clickable-row {{
            cursor: pointer;
            transition: background-color 0.2s;
        }}
        
        .clickable-row:hover {{
            background-color: #e3f2fd !important;
        }}
        
        .missing {{
            color: #999;
            font-style: italic;
            text-align: center;
        }}
        
        /* Modal styles */
        .modal {{
            display: none;
            position: fixed;
            z-index: 1000;
            left: 0;
            top: 0;
            width: 100%;
            height: 100%;
            background-color: rgba(0,0,0,0.5);
        }}
        
        .modal-content {{
            background-color: white;
            margin: 3% auto;
            padding: 30px;
            border-radius: 10px;
            width: 95%;
            max-width: 1400px;
            max-height: 85vh;
            overflow-y: auto;
        }}
        
        .modal-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 20px;
            padding-bottom: 10px;
            border-bottom: 1px solid #ddd;
        }}
        
        .modal-title {{
            color: #667eea;
            font-size: 1.5em;
            margin: 0;
        }}
        
        .close {{
            color: #aaa;
            font-size: 28px;
            font-weight: bold;
            cursor: pointer;
        }}
        
        .close:hover {{
            color: #000;
        }}
        
        .detail-table {{
            width: 100%;
            border-collapse: collapse;
            margin-top: 15px;
        }}
        
        .detail-table th {{
            background-color: #f8f9fa;
            padding: 10px;
            text-align: left;
            border-bottom: 2px solid #ddd;
            white-space: nowrap;
        }}
        
        .detail-table td {{
            padding: 10px;
            border-bottom: 1px solid #eee;
            vertical-align: top;
            white-space: nowrap;
        }}
        
        .detail-table .inventory-name {{
            font-weight: bold;
            color: #667eea;
        }}
    </style>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
</head>
<body>
    <div class="container">
        <!-- Header -->
        <div class="header">
            <h1>📊 File Inventory Analysis</h1>
            <p class="subtitle">Comparative analysis of {len(self.inventories)} file inventories using MD5 checksums</p>
        </div>
        
        <!-- Statistics -->
        <div class="stats-grid">
            <div class="stat-card">
                <div class="stat-value">{len(self.inventories)}</div>
                <div class="stat-label">Inventories</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{analysis['total_unique_files']:,}</div>
                <div class="stat-label">Unique Files</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{len(analysis['duplicates']):,}</div>
                <div class="stat-label">Duplicate Files</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{len(analysis['common_files']):,}</div>
                <div class="stat-label">Common Files</div>
            </div>
        </div>
        
        <!-- Inventory Summary Table -->
        <div class="section">
            <h2>📋 Inventory Summary</h2>
            <div class="section-content">
                <table>
                    <thead>
                        <tr>
                            <th>Inventory Name</th>
                            <th>File Name</th>
                            <th title="Total rows read from CSV file (excluding LRF files)">Total Rows ℹ️</th>
                            <th title="Files with valid MD5 checksums (excluding ERROR entries)">Valid Files ℹ️</th>
                            <th title="Distinct files in this inventory (same as Valid Files - shows unique checksums per inventory)">Unique Files ℹ️</th>
                        </tr>
                    </thead>
                    <tbody>
                        {inventory_table_rows}
                    </tbody>
                </table>
            </div>
        </div>
        
        <!-- Debug Summary Table -->
        <div class="section">
            <h2 class="collapsible-header" onclick="toggleSection('debug')" style="cursor: pointer;">🔍 Debug Summary (Processing Details) <span id="debug-indicator">▼</span></h2>
            <div id="debug-content" class="section-content collapsible-content" style="display: none;">
                <h3>📊 Processing Statistics</h3>
                <table>
                    <thead>
                        <tr>
                            <th>Inventory Name</th>
                            <th>Total Rows</th>
                            <th>Processed Files</th>
                            <th>Skipped Invalid</th>
                            <th>Empty Checksum</th>
                            <th>ERROR Checksum</th>
                            <th>Duplicate Checksums</th>
                        </tr>
                    </thead>
                    <tbody>
                        {debug_table_rows}
                    </tbody>
                </table>
                
                <h3>📋 Invalid Entries Details (First 20 per inventory)</h3>
                <table>
                    <thead>
                        <tr>
                            <th>Inventory</th>
                            <th>Filename</th>
                            <th>Checksum</th>
                            <th>Relative Path</th>
                            <th>Skip Reason</th>
                        </tr>
                    </thead>
                    <tbody>
                        {debug_details_rows}
                    </tbody>
                </table>
                
                <p><small><strong>Note:</strong> This debug section can be disabled by commenting out the debug code.</small></p>
            </div>
        </div>
        
        <!-- Files Comparison Table -->
        {self._generate_files_comparison_table()}
        
        <!-- File Distribution Chart -->
        <div class="section">
            <h2>📈 File Distribution Analysis</h2>
            <div class="section-content">
                <p>This chart shows how many files appear in multiple inventories:</p>
                <div class="chart-container">
                    <canvas id="distributionChart"></canvas>
                </div>
            </div>
        </div>
        
        <!-- Duplicate Files -->
        {'<div class="section"><h2 class="collapsible-header" onclick="toggleSection(\'duplicates\')" style="cursor: pointer;">🔄 Duplicate Files (Found in Multiple Inventories) <span id="duplicates-indicator">▼</span></h2><div id="duplicates-content" class="section-content collapsible-content" style="display: none;"><p>Files with identical MD5 checksums found across different inventories:</p><table><thead><tr><th>Checksum</th><th>Filename</th><th>Path</th><th>Count</th><th>Found In</th></tr></thead><tbody>' + duplicates_rows + '</tbody></table>' + (f'<p><small>Showing first 50 of {len(analysis["duplicates"])} duplicates...</small></p>' if len(analysis["duplicates"]) > 50 else '') + '</div></div>' if analysis["duplicates"] else ''}
        
        <!-- Common Files -->
        {'<div class="section"><h2 class="collapsible-header" onclick="toggleSection(\'common\')" style="cursor: pointer;">🤝 Common Files (Present in All Inventories) <span id="common-indicator">▼</span></h2><div id="common-content" class="section-content collapsible-content" style="display: none;"><p>Files found in every inventory:</p><table><thead><tr><th>Checksum</th><th>Filename</th><th>Path</th><th>Modified</th></tr></thead><tbody>' + common_rows + '</tbody></table>' + (f'<p><small>Showing first 20 of {len(analysis["common_files"])} common files...</small></p>' if len(analysis["common_files"]) > 20 else '') + '</div></div>' if analysis["common_files"] else ''}
        
        <!-- Unique Files per Inventory -->
        <div class="section">
            <h2 class="collapsible-header" onclick="toggleSection('unique')" style="cursor: pointer;">📁 Files Unique to Each Inventory <span id="unique-indicator">▼</span></h2>
            <div id="unique-content" class="section-content collapsible-content" style="display: none;">
                {unique_sections}
            </div>
        </div>
        
        <div class="timestamp">
            Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        </div>
    </div>
    
    <!-- File Details Modal -->
    <div id="fileDetailsModal" class="modal">
        <div class="modal-content">
            <div class="modal-header">
                <h2 class="modal-title">File Details</h2>
                <span class="close" onclick="closeModal()">&times;</span>
            </div>
            <div id="modalBody">
                <!-- Content will be populated by JavaScript -->
            </div>
        </div>
    </div>
    
    <script>
        // File Distribution Chart
        const ctx = document.getElementById('distributionChart').getContext('2d');
        new Chart(ctx, {{
            type: 'bar',
            data: {{
                labels: [{','.join([f"'In {i} inventor{'y' if i==1 else 'ies'}'" for i in sorted(analysis['file_distribution'].keys())])}],
                datasets: [{{
                    label: 'Number of Files',
                    data: [{','.join([str(analysis['file_distribution'][i]) for i in sorted(analysis['file_distribution'].keys())])}],
                    backgroundColor: 'rgba(102, 126, 234, 0.8)',
                    borderColor: 'rgba(102, 126, 234, 1)',
                    borderWidth: 1
                }}]
            }},
            options: {{
                responsive: true,
                maintainAspectRatio: false,
                scales: {{
                    y: {{
                        beginAtZero: true,
                        title: {{
                            display: true,
                            text: 'Number of Files'
                        }}
                    }},
                    x: {{
                        title: {{
                            display: true,
                            text: 'Inventory Presence'
                        }}
                    }}
                }},
                plugins: {{
                    title: {{
                        display: true,
                        text: 'File Distribution Across Inventories'
                    }},
                    legend: {{
                        display: false
                    }}
                }}
            }}
        }});
        
        // Modal functionality
        document.addEventListener('DOMContentLoaded', function() {{
            // Add click event listeners to table rows
            const table = document.getElementById('filesTable');
            if (table) {{
                table.addEventListener('click', function(e) {{
                    const row = e.target.closest('tr.clickable-row');
                    if (row && row.dataset.fileInfo) {{
                        showFileDetails(row.dataset.fileInfo);
                    }}
                }});
            }}
        }});
        
        function showFileDetails(dataJson) {{
            const data = JSON.parse(dataJson);
            const modal = document.getElementById('fileDetailsModal');
            const modalBody = document.getElementById('modalBody');
            
            let html = `
                <div style="margin-bottom: 20px;">
                    <h3>File #${{data.counter}}</h3>
                    <p><strong>MD5 Checksum:</strong> <code>${{data.checksum}}</code></p>
                </div>
                
                <table class="detail-table">
                    <thead>
                        <tr>
                            <th>Inventory</th>
                            <th>Filename</th>
                            <th>Relative Path</th>
                            <th>Modify Time</th>
                        </tr>
                    </thead>
                    <tbody>
            `;
            
            for (const [invName, fileInfo] of Object.entries(data.files)) {{
                if (fileInfo) {{
                    html += `
                        <tr>
                            <td class="inventory-name">${{invName}}</td>
                            <td>${{fileInfo.filename}}</td>
                            <td>${{fileInfo.relative_path || '-'}}</td>
                            <td>${{fileInfo.modify_time || '-'}}</td>
                        </tr>
                    `;
                }} else {{
                    html += `
                        <tr>
                            <td class="inventory-name">${{invName}}</td>
                            <td colspan="3" style="color: #999; font-style: italic; text-align: center;">File not found in this inventory</td>
                        </tr>
                    `;
                }}
            }}
            
            html += `
                    </tbody>
                </table>
            `;
            
            modalBody.innerHTML = html;
            modal.style.display = 'block';
        }}
        
        function closeModal() {{
            document.getElementById('fileDetailsModal').style.display = 'none';
        }}
        
        // Close modal when clicking outside of it
        window.onclick = function(event) {{
            const modal = document.getElementById('fileDetailsModal');
            if (event.target === modal) {{
                modal.style.display = 'none';
            }}
        }}
        
        // Toggle section visibility
        function toggleSection(sectionId) {{
            const content = document.getElementById(sectionId + '-content');
            const indicator = document.getElementById(sectionId + '-indicator');
            
            if (content.style.display === 'none' || content.style.display === '') {{
                content.style.display = 'block';
                indicator.textContent = '▲';
            }} else {{
                content.style.display = 'none';
                indicator.textContent = '▼';
            }}
        }}
        
        // Toggle all files display with scrollable view
        function toggleAllFiles() {{
            const tableContainer = document.getElementById('tableContainer');
            const button = document.getElementById('showAllBtn');
            const allRows = document.querySelectorAll('.all-files-row');
            
            if (button.textContent.includes('Show All Files')) {{
                // Show all files and make container scrollable
                allRows.forEach(row => {{
                    row.style.display = 'table-row';
                }});
                
                // Add scrollable styling
                tableContainer.classList.add('scrollable');
                tableContainer.style.maxHeight = '600px';
                tableContainer.style.overflowY = 'auto';
                tableContainer.style.border = '1px solid #ddd';
                
                button.textContent = 'Show Less Files';
                
                // Scroll to top of table
                tableContainer.scrollTop = 0;
            }} else {{
                // Hide extra files and remove scrolling
                allRows.forEach((row, index) => {{
                    if (index >= 200) {{
                        row.style.display = 'none';
                    }}
                }});
                
                // Remove scrollable styling
                tableContainer.classList.remove('scrollable');
                tableContainer.style.maxHeight = 'none';
                tableContainer.style.overflowY = 'visible';
                tableContainer.style.border = 'none';
                
                button.textContent = button.textContent.replace('Show Less Files', 'Show All Files');
            }}
        }}
    </script>
</body>
</html>
        """
        
        return html_template


def main():
    """Main function to handle command line arguments and generate analysis."""
    
    # Default configuration
    default_base_directory = "/Users/syuen/work_note/"
    default_csv_files = [
        "SanDisk_Video.csv",
        "SanDisk_Simon_media.csv", 
        "SSD_Videos_Original_Inc_Simon_iPhone.csv",
        "SSD_2025HKTrip_Organized_from_Original.csv"
    ]
    
    if len(sys.argv) < 2:
        # No parameters given - use default CSV files
        print("📁 No CSV files specified, using default configuration...")
        csv_files = [os.path.join(default_base_directory, csv_name) for csv_name in default_csv_files]
        print(f"   Base directory: {default_base_directory}")
        for csv_file in default_csv_files:
            print(f"   - {csv_file}")
    else:
        # Use provided CSV files
        csv_files = sys.argv[1:]
    
    # Initialize analyzer
    analyzer = FileInventoryAnalyzer()
    analyzer.logger.info(f"Command line arguments: {sys.argv}")
    analyzer.logger.info(f"Using {len(csv_files)} CSV files for analysis")
    
    # Load CSV files
    loaded_count = 0
    
    print("📁 Loading CSV inventories...")
    for csv_file in csv_files:
        if not os.path.exists(csv_file):
            print(f"⚠️  File not found: {csv_file}")
            analyzer.logger.error(f"CSV file not found: {csv_file}")
            continue
        
        print(f"   Loading: {csv_file}")
        result = analyzer.load_csv_inventory(csv_file)
        if result:
            debug_stats = result['debug_stats']
            print(f"   ✅ Loaded {result['total_files']} files ({result['unique_files']} unique)")
            if debug_stats['skipped_invalid'] > 0:
                print(f"      🔍 Debug: {debug_stats['total_rows']} total rows, {debug_stats['skipped_invalid']} skipped")
                if debug_stats['skipped_error_checksum'] > 0:
                    print(f"         - {debug_stats['skipped_error_checksum']} ERROR checksums")
                if debug_stats['skipped_empty_checksum'] > 0:
                    print(f"         - {debug_stats['skipped_empty_checksum']} empty checksums")
                if debug_stats['duplicate_checksums'] > 0:
                    print(f"         - {debug_stats['duplicate_checksums']} duplicate checksums")
            loaded_count += 1
        else:
            print(f"   ❌ Failed to load {csv_file}")
    
    if loaded_count == 0:
        print("❌ No CSV files were successfully loaded.")
        analyzer.logger.critical("No CSV files were successfully loaded. Exiting.")
        sys.exit(1)
    
    print(f"\n📊 Generating analysis for {loaded_count} inventories...")
    
    # Generate HTML report
    output_file = "file_inventory_analysis.html"
    try:
        report_path = analyzer.generate_html_report(output_file)
        print(f"✅ Analysis complete!")
        print(f"📄 HTML report saved: {report_path}")
        print(f"📄 Log file saved: {analyzer.log_file}")
        print(f"🌐 Open in browser: file://{os.path.abspath(report_path)}")
        
        # Log session completion
        analyzer.logger.info("="*80)
        analyzer.logger.info("File Inventory Analysis Session Completed Successfully")
        analyzer.logger.info(f"HTML Report: {os.path.abspath(report_path)}")
        analyzer.logger.info(f"Log File: {os.path.abspath(analyzer.log_file)}")
        analyzer.logger.info("="*80)
        
    except Exception as e:
        print(f"❌ Error generating report: {e}")
        analyzer.logger.critical(f"Critical error generating report: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()

