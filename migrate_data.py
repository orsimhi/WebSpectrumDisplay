#!/usr/bin/env python3
"""
RF Data Migration Utility

This script helps migrate existing RF amplitude data from files to the SQLite database.
Modify the parsing functions based on your current data format.
"""

import sqlite3
import json
import csv
import numpy as np
from datetime import datetime
import os
import argparse

class RFDataMigrator:
    def __init__(self, db_path='rf_data.db'):
        self.db_path = db_path
        self.setup_database()
    
    def setup_database(self):
        """Initialize the database if it doesn't exist"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS rf_amplitudes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                center_frequency REAL NOT NULL,
                span REAL NOT NULL,
                powers TEXT NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        conn.close()
        print(f"Database initialized: {self.db_path}")
    
    def migrate_json_file(self, file_path):
        """
        Migrate from JSON format:
        {
            "timestamp": "2024-01-01 12:00:00",
            "center_frequency": 2400.0,
            "span": 100.0,
            "powers": [...]
        }
        """
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
            
            if isinstance(data, list):
                # Multiple records in array
                records = data
            else:
                # Single record
                records = [data]
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            for record in records:
                cursor.execute('''
                    INSERT INTO rf_amplitudes (timestamp, center_frequency, span, powers)
                    VALUES (?, ?, ?, ?)
                ''', (
                    record['timestamp'],
                    record['center_frequency'],
                    record['span'],
                    json.dumps(record['powers'])
                ))
            
            conn.commit()
            conn.close()
            print(f"Migrated {len(records)} records from {file_path}")
            
        except Exception as e:
            print(f"Error migrating JSON file {file_path}: {e}")
    
    def migrate_csv_file(self, file_path, center_freq, span, timestamp_col=None):
        """
        Migrate from CSV format where each row contains power measurements
        
        Args:
            file_path: Path to CSV file
            center_freq: Center frequency in MHz
            span: Frequency span in MHz
            timestamp_col: Column name for timestamp (if None, uses current time)
        """
        try:
            import pandas as pd
            df = pd.read_csv(file_path)
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            for idx, row in df.iterrows():
                # Extract timestamp
                if timestamp_col and timestamp_col in df.columns:
                    timestamp = str(row[timestamp_col])
                else:
                    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                
                # Get power values (all numeric columns)
                powers = []
                for col in df.columns:
                    if col != timestamp_col and pd.api.types.is_numeric_dtype(df[col]):
                        powers.append(float(row[col]))
                
                cursor.execute('''
                    INSERT INTO rf_amplitudes (timestamp, center_frequency, span, powers)
                    VALUES (?, ?, ?, ?)
                ''', (timestamp, center_freq, span, json.dumps(powers)))
            
            conn.commit()
            conn.close()
            print(f"Migrated {len(df)} records from {file_path}")
            
        except Exception as e:
            print(f"Error migrating CSV file {file_path}: {e}")
    
    def migrate_numpy_file(self, file_path, center_freq, span, timestamp=None):
        """
        Migrate from numpy .npy format
        
        Args:
            file_path: Path to .npy file
            center_freq: Center frequency in MHz
            span: Frequency span in MHz
            timestamp: Timestamp string (if None, uses current time)
        """
        try:
            data = np.load(file_path)
            
            if timestamp is None:
                timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            # Handle different numpy array shapes
            if data.ndim == 1:
                # Single measurement
                powers = data.tolist()
                records = [(timestamp, center_freq, span, powers)]
            elif data.ndim == 2:
                # Multiple measurements (each row is a measurement)
                records = []
                for i, row in enumerate(data):
                    ts = f"{timestamp}_{i:04d}" if len(data) > 1 else timestamp
                    records.append((ts, center_freq, span, row.tolist()))
            else:
                raise ValueError("Unsupported numpy array shape")
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            for ts, cf, sp, powers in records:
                cursor.execute('''
                    INSERT INTO rf_amplitudes (timestamp, center_frequency, span, powers)
                    VALUES (?, ?, ?, ?)
                ''', (ts, cf, sp, json.dumps(powers)))
            
            conn.commit()
            conn.close()
            print(f"Migrated {len(records)} records from {file_path}")
            
        except Exception as e:
            print(f"Error migrating numpy file {file_path}: {e}")
    
    def migrate_text_file(self, file_path, center_freq, span, delimiter=None):
        """
        Migrate from text file where each line contains space/comma-separated power values
        
        Args:
            file_path: Path to text file
            center_freq: Center frequency in MHz
            span: Frequency span in MHz
            delimiter: Value delimiter (None for whitespace)
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            records_count = 0
            with open(file_path, 'r') as f:
                for line_num, line in enumerate(f, 1):
                    line = line.strip()
                    if not line or line.startswith('#'):
                        continue
                    
                    try:
                        values = line.split(delimiter)
                        powers = [float(val) for val in values if val.strip()]
                        
                        timestamp = datetime.now().strftime(f'%Y-%m-%d %H:%M:%S_{line_num:04d}')
                        
                        cursor.execute('''
                            INSERT INTO rf_amplitudes (timestamp, center_frequency, span, powers)
                            VALUES (?, ?, ?, ?)
                        ''', (timestamp, center_freq, span, json.dumps(powers)))
                        
                        records_count += 1
                    except ValueError:
                        print(f"Skipping invalid line {line_num}: {line[:50]}...")
            
            conn.commit()
            conn.close()
            print(f"Migrated {records_count} records from {file_path}")
            
        except Exception as e:
            print(f"Error migrating text file {file_path}: {e}")
    
    def migrate_directory(self, directory_path, file_pattern="*.json", **kwargs):
        """
        Migrate all files matching a pattern in a directory
        
        Args:
            directory_path: Path to directory
            file_pattern: File pattern (e.g., "*.json", "*.csv")
            **kwargs: Additional arguments for specific migration functions
        """
        import glob
        
        pattern_path = os.path.join(directory_path, file_pattern)
        files = glob.glob(pattern_path)
        
        if not files:
            print(f"No files found matching pattern: {pattern_path}")
            return
        
        print(f"Found {len(files)} files to migrate")
        
        for file_path in files:
            print(f"Processing: {file_path}")
            
            if file_pattern.endswith(".json"):
                self.migrate_json_file(file_path)
            elif file_pattern.endswith(".csv"):
                self.migrate_csv_file(file_path, **kwargs)
            elif file_pattern.endswith(".npy"):
                self.migrate_numpy_file(file_path, **kwargs)
            elif file_pattern.endswith(".txt"):
                self.migrate_text_file(file_path, **kwargs)
            else:
                print(f"Unknown file type: {file_path}")
    
    def export_to_json(self, output_file="rf_data_export.json"):
        """Export all database records to JSON format"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT timestamp, center_frequency, span, powers 
                FROM rf_amplitudes 
                ORDER BY timestamp
            ''')
            
            records = []
            for row in cursor.fetchall():
                record = {
                    'timestamp': row[0],
                    'center_frequency': row[1],
                    'span': row[2],
                    'powers': json.loads(row[3])
                }
                records.append(record)
            
            with open(output_file, 'w') as f:
                json.dump(records, f, indent=2)
            
            conn.close()
            print(f"Exported {len(records)} records to {output_file}")
            
        except Exception as e:
            print(f"Error exporting to JSON: {e}")
    
    def clear_database(self):
        """Clear all records from the database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('DELETE FROM rf_amplitudes')
        conn.commit()
        conn.close()
        print("Database cleared")

def main():
    parser = argparse.ArgumentParser(description='RF Data Migration Utility')
    parser.add_argument('--db', default='rf_data.db', help='Database file path')
    parser.add_argument('--clear', action='store_true', help='Clear database before migration')
    parser.add_argument('--export', help='Export database to JSON file')
    
    # Migration options
    parser.add_argument('--json', help='Migrate from JSON file')
    parser.add_argument('--csv', help='Migrate from CSV file')
    parser.add_argument('--numpy', help='Migrate from numpy .npy file')
    parser.add_argument('--text', help='Migrate from text file')
    parser.add_argument('--directory', help='Migrate all files from directory')
    parser.add_argument('--pattern', default='*.json', help='File pattern for directory migration')
    
    # RF parameters
    parser.add_argument('--center-freq', type=float, help='Center frequency in MHz')
    parser.add_argument('--span', type=float, help='Frequency span in MHz')
    parser.add_argument('--timestamp', help='Timestamp for the measurement')
    
    args = parser.parse_args()
    
    # Initialize migrator
    migrator = RFDataMigrator(args.db)
    
    # Clear database if requested
    if args.clear:
        migrator.clear_database()
    
    # Export if requested
    if args.export:
        migrator.export_to_json(args.export)
        return
    
    # Perform migrations
    if args.json:
        migrator.migrate_json_file(args.json)
    
    if args.csv:
        if not args.center_freq or not args.span:
            print("Error: --center-freq and --span required for CSV migration")
            return
        migrator.migrate_csv_file(args.csv, args.center_freq, args.span)
    
    if args.numpy:
        if not args.center_freq or not args.span:
            print("Error: --center-freq and --span required for numpy migration")
            return
        migrator.migrate_numpy_file(args.numpy, args.center_freq, args.span, args.timestamp)
    
    if args.text:
        if not args.center_freq or not args.span:
            print("Error: --center-freq and --span required for text migration")
            return
        migrator.migrate_text_file(args.text, args.center_freq, args.span)
    
    if args.directory:
        kwargs = {}
        if args.center_freq:
            kwargs['center_freq'] = args.center_freq
        if args.span:
            kwargs['span'] = args.span
        if args.timestamp:
            kwargs['timestamp'] = args.timestamp
        
        migrator.migrate_directory(args.directory, args.pattern, **kwargs)

if __name__ == "__main__":
    main()