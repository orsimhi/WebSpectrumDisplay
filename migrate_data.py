#!/usr/bin/env python3
"""
RF Data Migration Utility for Time-Series Database

This script helps migrate existing RF amplitude data from files to InfluxDB.
Supports NDJSON format for streaming data ingestion.
"""

import json
import csv
import numpy as np
from datetime import datetime, timezone
import os
import argparse
from influxdb_client import InfluxDBClient, Point, WritePrecision
from influxdb_client.client.write_api import SYNCHRONOUS
import pandas as pd

class RFDataMigrator:
    def __init__(self, influxdb_url="http://localhost:8086", 
                 token="rf-amplitude-token", 
                 org="rf-org", 
                 bucket="rf-amplitude-data"):
        self.influxdb_url = influxdb_url
        self.token = token
        self.org = org
        self.bucket = bucket
        self.client = None
        self.write_api = None
        self.setup_influxdb()
    
    def setup_influxdb(self):
        """Initialize InfluxDB connection"""
        try:
            self.client = InfluxDBClient(
                url=self.influxdb_url,
                token=self.token,
                org=self.org
            )
            
            # Test connection
            health = self.client.health()
            if health.status == "pass":
                print(f"✓ Connected to InfluxDB at {self.influxdb_url}")
                self.write_api = self.client.write_api(write_options=SYNCHRONOUS)
            else:
                raise Exception(f"InfluxDB health check failed: {health.status}")
                
        except Exception as e:
            print(f"❌ Failed to connect to InfluxDB: {e}")
            print("Make sure InfluxDB is running and accessible")
            raise
    
    def migrate_ndjson_file(self, file_path, device_id="spectrum_analyzer", location="lab"):
        """
        Migrate from NDJSON format (newline-delimited JSON)
        Each line contains a complete RF measurement event:
        {"timestamp": "2024-01-01T12:00:00Z", "center_frequency": 2400.0, "span": 100.0, "powers": [...]}
        """
        try:
            records_count = 0
            with open(file_path, 'r') as f:
                for line_num, line in enumerate(f, 1):
                    line = line.strip()
                    if not line:
                        continue
                    
                    try:
                        record = json.loads(line)
                        
                        # Parse timestamp
                        if 'timestamp' in record:
                            if isinstance(record['timestamp'], str):
                                timestamp = pd.to_datetime(record['timestamp'])
                            else:
                                timestamp = datetime.fromtimestamp(record['timestamp'], tz=timezone.utc)
                        else:
                            timestamp = datetime.now(timezone.utc)
                        
                        # Extract RF data
                        center_frequency = record.get('center_frequency', 0)
                        span = record.get('span', 0)
                        powers = record.get('powers', [])
                        
                        # Additional metadata
                        device_id_val = record.get('device_id', device_id)
                        location_val = record.get('location', location)
                        
                        # Create InfluxDB point
                        point = Point("rf_amplitude") \
                            .tag("device_id", device_id_val) \
                            .tag("location", location_val) \
                            .field("center_frequency", float(center_frequency)) \
                            .field("span", float(span)) \
                            .field("powers", json.dumps(powers)) \
                            .field("num_points", len(powers)) \
                            .time(timestamp, WritePrecision.NS)
                        
                        # Additional fields from record
                        for key, value in record.items():
                            if key not in ['timestamp', 'center_frequency', 'span', 'powers', 'device_id', 'location']:
                                if isinstance(value, (int, float)):
                                    point = point.field(key, value)
                                elif isinstance(value, str) and len(value) < 255:
                                    point = point.tag(key, value)
                        
                        self.write_api.write(bucket=self.bucket, org=self.org, record=point)
                        records_count += 1
                        
                        if records_count % 100 == 0:
                            print(f"  Processed {records_count} records...")
                            
                    except json.JSONDecodeError as e:
                        print(f"❌ Invalid JSON on line {line_num}: {e}")
                        continue
                    except Exception as e:
                        print(f"❌ Error processing line {line_num}: {e}")
                        continue
            
            print(f"✓ Migrated {records_count} records from {file_path}")
            
        except Exception as e:
            print(f"❌ Error migrating NDJSON file {file_path}: {e}")
    
    def migrate_json_file(self, file_path, device_id="spectrum_analyzer", location="lab"):
        """
        Migrate from standard JSON format:
        Single object or array of objects with RF measurement data
        """
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
            
            if isinstance(data, list):
                records = data
            else:
                records = [data]
            
            records_count = 0
            for record in records:
                # Parse timestamp
                if 'timestamp' in record:
                    if isinstance(record['timestamp'], str):
                        timestamp = pd.to_datetime(record['timestamp'])
                    else:
                        timestamp = datetime.fromtimestamp(record['timestamp'], tz=timezone.utc)
                else:
                    timestamp = datetime.now(timezone.utc)
                
                center_frequency = record.get('center_frequency', 0)
                span = record.get('span', 0)
                powers = record.get('powers', [])
                device_id_val = record.get('device_id', device_id)
                location_val = record.get('location', location)
                
                point = Point("rf_amplitude") \
                    .tag("device_id", device_id_val) \
                    .tag("location", location_val) \
                    .field("center_frequency", float(center_frequency)) \
                    .field("span", float(span)) \
                    .field("powers", json.dumps(powers)) \
                    .field("num_points", len(powers)) \
                    .time(timestamp, WritePrecision.NS)
                
                self.write_api.write(bucket=self.bucket, org=self.org, record=point)
                records_count += 1
            
            print(f"✓ Migrated {records_count} records from {file_path}")
            
        except Exception as e:
            print(f"❌ Error migrating JSON file {file_path}: {e}")
    
    def migrate_csv_file(self, file_path, center_freq, span, timestamp_col=None, 
                        device_id="spectrum_analyzer", location="lab"):
        """
        Migrate from CSV format where each row contains power measurements
        """
        try:
            df = pd.read_csv(file_path)
            
            records_count = 0
            for idx, row in df.iterrows():
                # Extract timestamp
                if timestamp_col and timestamp_col in df.columns:
                    timestamp = pd.to_datetime(row[timestamp_col])
                else:
                    timestamp = datetime.now(timezone.utc)
                
                # Get power values (all numeric columns except timestamp)
                powers = []
                for col in df.columns:
                    if col != timestamp_col and pd.api.types.is_numeric_dtype(df[col]):
                        powers.append(float(row[col]))
                
                point = Point("rf_amplitude") \
                    .tag("device_id", device_id) \
                    .tag("location", location) \
                    .field("center_frequency", float(center_freq)) \
                    .field("span", float(span)) \
                    .field("powers", json.dumps(powers)) \
                    .field("num_points", len(powers)) \
                    .time(timestamp, WritePrecision.NS)
                
                self.write_api.write(bucket=self.bucket, org=self.org, record=point)
                records_count += 1
                
                if records_count % 100 == 0:
                    print(f"  Processed {records_count} records...")
            
            print(f"✓ Migrated {records_count} records from {file_path}")
            
        except Exception as e:
            print(f"❌ Error migrating CSV file {file_path}: {e}")
    
    def migrate_numpy_file(self, file_path, center_freq, span, timestamp=None,
                          device_id="spectrum_analyzer", location="lab"):
        """
        Migrate from numpy .npy format
        """
        try:
            data = np.load(file_path)
            
            if timestamp is None:
                timestamp = datetime.now(timezone.utc)
            else:
                timestamp = pd.to_datetime(timestamp)
            
            records_count = 0
            # Handle different numpy array shapes
            if data.ndim == 1:
                # Single measurement
                powers = data.tolist()
                
                point = Point("rf_amplitude") \
                    .tag("device_id", device_id) \
                    .tag("location", location) \
                    .field("center_frequency", float(center_freq)) \
                    .field("span", float(span)) \
                    .field("powers", json.dumps(powers)) \
                    .field("num_points", len(powers)) \
                    .time(timestamp, WritePrecision.NS)
                
                self.write_api.write(bucket=self.bucket, org=self.org, record=point)
                records_count = 1
                
            elif data.ndim == 2:
                # Multiple measurements (each row is a measurement)
                for i, row in enumerate(data):
                    ts = timestamp + pd.Timedelta(seconds=i) if len(data) > 1 else timestamp
                    powers = row.tolist()
                    
                    point = Point("rf_amplitude") \
                        .tag("device_id", device_id) \
                        .tag("location", location) \
                        .field("center_frequency", float(center_freq)) \
                        .field("span", float(span)) \
                        .field("powers", json.dumps(powers)) \
                        .field("num_points", len(powers)) \
                        .time(ts, WritePrecision.NS)
                    
                    self.write_api.write(bucket=self.bucket, org=self.org, record=point)
                    records_count += 1
                    
                    if records_count % 100 == 0:
                        print(f"  Processed {records_count} records...")
            else:
                raise ValueError("Unsupported numpy array shape")
            
            print(f"✓ Migrated {records_count} records from {file_path}")
            
        except Exception as e:
            print(f"❌ Error migrating numpy file {file_path}: {e}")
    
    def migrate_directory(self, directory_path, file_pattern="*.ndjson", **kwargs):
        """
        Migrate all files matching a pattern in a directory
        """
        import glob
        
        pattern_path = os.path.join(directory_path, file_pattern)
        files = glob.glob(pattern_path)
        
        if not files:
            print(f"❌ No files found matching pattern: {pattern_path}")
            return
        
        print(f"📁 Found {len(files)} files to migrate")
        
        for file_path in files:
            print(f"📄 Processing: {file_path}")
            
            if file_pattern.endswith(".ndjson"):
                self.migrate_ndjson_file(file_path, **kwargs)
            elif file_pattern.endswith(".json"):
                self.migrate_json_file(file_path, **kwargs)
            elif file_pattern.endswith(".csv"):
                self.migrate_csv_file(file_path, **kwargs)
            elif file_pattern.endswith(".npy"):
                self.migrate_numpy_file(file_path, **kwargs)
            else:
                print(f"❓ Unknown file type: {file_path}")
    
    def stream_ndjson_data(self, file_path, batch_size=100, device_id="spectrum_analyzer", location="lab"):
        """
        Stream NDJSON data in batches for real-time processing
        """
        try:
            batch = []
            records_count = 0
            
            with open(file_path, 'r') as f:
                for line_num, line in enumerate(f, 1):
                    line = line.strip()
                    if not line:
                        continue
                    
                    try:
                        record = json.loads(line)
                        
                        # Parse timestamp
                        if 'timestamp' in record:
                            if isinstance(record['timestamp'], str):
                                timestamp = pd.to_datetime(record['timestamp'])
                            else:
                                timestamp = datetime.fromtimestamp(record['timestamp'], tz=timezone.utc)
                        else:
                            timestamp = datetime.now(timezone.utc)
                        
                        center_frequency = record.get('center_frequency', 0)
                        span = record.get('span', 0)
                        powers = record.get('powers', [])
                        device_id_val = record.get('device_id', device_id)
                        location_val = record.get('location', location)
                        
                        point = Point("rf_amplitude") \
                            .tag("device_id", device_id_val) \
                            .tag("location", location_val) \
                            .field("center_frequency", float(center_frequency)) \
                            .field("span", float(span)) \
                            .field("powers", json.dumps(powers)) \
                            .field("num_points", len(powers)) \
                            .time(timestamp, WritePrecision.NS)
                        
                        batch.append(point)
                        
                        # Write batch when it's full
                        if len(batch) >= batch_size:
                            self.write_api.write(bucket=self.bucket, org=self.org, record=batch)
                            records_count += len(batch)
                            print(f"  📊 Streamed batch of {len(batch)} records (total: {records_count})")
                            batch = []
                        
                    except Exception as e:
                        print(f"❌ Error processing line {line_num}: {e}")
                        continue
                
                # Write remaining batch
                if batch:
                    self.write_api.write(bucket=self.bucket, org=self.org, record=batch)
                    records_count += len(batch)
                    print(f"  📊 Streamed final batch of {len(batch)} records")
            
            print(f"✓ Streamed {records_count} records from {file_path}")
            
        except Exception as e:
            print(f"❌ Error streaming NDJSON file {file_path}: {e}")
    
    def export_to_ndjson(self, output_file="rf_data_export.ndjson", time_range="-24h"):
        """Export InfluxDB data to NDJSON format"""
        try:
            query_api = self.client.query_api()
            query = f'''
                from(bucket: "{self.bucket}")
                |> range(start: {time_range})
                |> filter(fn: (r) => r["_measurement"] == "rf_amplitude")
                |> pivot(rowKey:["_time"], columnKey: ["_field"], valueColumn: "_value")
                |> sort(columns: ["_time"], desc: false)
            '''
            
            result = query_api.query(query)
            records_count = 0
            
            with open(output_file, 'w') as f:
                for table in result:
                    for record in table.records:
                        export_record = {
                            'timestamp': record.get_time().isoformat(),
                            'center_frequency': record.values.get('center_frequency', 0),
                            'span': record.values.get('span', 0),
                            'powers': json.loads(record.values.get('powers', '[]')),
                            'device_id': record.values.get('device_id', 'unknown'),
                            'location': record.values.get('location', 'unknown')
                        }
                        
                        f.write(json.dumps(export_record) + '\n')
                        records_count += 1
            
            print(f"✓ Exported {records_count} records to {output_file}")
            
        except Exception as e:
            print(f"❌ Error exporting to NDJSON: {e}")
    
    def clear_bucket(self):
        """Clear all data from the bucket"""
        try:
            delete_api = self.client.delete_api()
            delete_api.delete(
                start="1970-01-01T00:00:00Z",
                stop=datetime.now(timezone.utc),
                predicate='_measurement="rf_amplitude"',
                bucket=self.bucket,
                org=self.org
            )
            print(f"✓ Cleared all data from bucket: {self.bucket}")
            
        except Exception as e:
            print(f"❌ Error clearing bucket: {e}")
    
    def close(self):
        """Close InfluxDB connection"""
        if self.client:
            self.client.close()

def main():
    parser = argparse.ArgumentParser(description='RF Data Migration Utility for InfluxDB')
    parser.add_argument('--url', default='http://localhost:8086', help='InfluxDB URL')
    parser.add_argument('--token', default='rf-amplitude-token', help='InfluxDB token')
    parser.add_argument('--org', default='rf-org', help='InfluxDB organization')
    parser.add_argument('--bucket', default='rf-amplitude-data', help='InfluxDB bucket')
    parser.add_argument('--clear', action='store_true', help='Clear bucket before migration')
    parser.add_argument('--export', help='Export bucket data to NDJSON file')
    parser.add_argument('--time-range', default='-24h', help='Time range for export (e.g., -24h, -7d)')
    
    # Migration options
    parser.add_argument('--ndjson', help='Migrate from NDJSON file')
    parser.add_argument('--json', help='Migrate from JSON file')
    parser.add_argument('--csv', help='Migrate from CSV file')
    parser.add_argument('--numpy', help='Migrate from numpy .npy file')
    parser.add_argument('--directory', help='Migrate all files from directory')
    parser.add_argument('--pattern', default='*.ndjson', help='File pattern for directory migration')
    parser.add_argument('--stream', help='Stream NDJSON file in batches')
    parser.add_argument('--batch-size', type=int, default=100, help='Batch size for streaming')
    
    # RF parameters
    parser.add_argument('--center-freq', type=float, help='Center frequency in MHz')
    parser.add_argument('--span', type=float, help='Frequency span in MHz')
    parser.add_argument('--timestamp', help='Timestamp for the measurement')
    parser.add_argument('--device-id', default='spectrum_analyzer', help='Device ID tag')
    parser.add_argument('--location', default='lab', help='Location tag')
    
    args = parser.parse_args()
    
    print("RF Data Migration Utility for InfluxDB")
    print("=" * 50)
    
    # Initialize migrator
    try:
        migrator = RFDataMigrator(args.url, args.token, args.org, args.bucket)
    except Exception as e:
        print(f"❌ Failed to initialize migrator: {e}")
        return 1
    
    try:
        # Clear bucket if requested
        if args.clear:
            migrator.clear_bucket()
        
        # Export if requested
        if args.export:
            migrator.export_to_ndjson(args.export, args.time_range)
            return 0
        
        # Perform migrations
        if args.ndjson:
            migrator.migrate_ndjson_file(args.ndjson, args.device_id, args.location)
        
        if args.json:
            migrator.migrate_json_file(args.json, args.device_id, args.location)
        
        if args.csv:
            if not args.center_freq or not args.span:
                print("❌ Error: --center-freq and --span required for CSV migration")
                return 1
            migrator.migrate_csv_file(args.csv, args.center_freq, args.span, 
                                    device_id=args.device_id, location=args.location)
        
        if args.numpy:
            if not args.center_freq or not args.span:
                print("❌ Error: --center-freq and --span required for numpy migration")
                return 1
            migrator.migrate_numpy_file(args.numpy, args.center_freq, args.span, 
                                      args.timestamp, args.device_id, args.location)
        
        if args.stream:
            migrator.stream_ndjson_data(args.stream, args.batch_size, args.device_id, args.location)
        
        if args.directory:
            kwargs = {
                'device_id': args.device_id,
                'location': args.location
            }
            if args.center_freq:
                kwargs['center_freq'] = args.center_freq
            if args.span:
                kwargs['span'] = args.span
            if args.timestamp:
                kwargs['timestamp'] = args.timestamp
            
            migrator.migrate_directory(args.directory, args.pattern, **kwargs)
        
        if not any([args.ndjson, args.json, args.csv, args.numpy, args.stream, args.directory]):
            print("ℹ️  No migration options specified. Use --help for available options.")
            
    finally:
        migrator.close()
    
    return 0

if __name__ == "__main__":
    exit(main())