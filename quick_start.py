#!/usr/bin/env python3
"""
Quick Start Script for WebSpectrumDisplay TimescaleDB Migration

This script demonstrates the complete workflow:
1. Test database connection
2. Setup database schema
3. Migrate sample data
4. Query and display results
"""

import sys
import logging
from pathlib import Path
from datetime import datetime, timedelta

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def main():
    print("=" * 60)
    print("    WebSpectrumDisplay TimescaleDB Quick Start")
    print("=" * 60)
    print()
    
    try:
        # Import our modules
        from database import db_manager
        from ndjson_migrator import NDJSONMigrator
        
        # Step 1: Test database connection
        print("🔗 Step 1: Testing database connection...")
        try:
            stats = db_manager.get_statistics()
            print("✅ Database connection successful!")
            print(f"   Current records: {stats.get('total_records', 0)}")
        except Exception as e:
            print(f"❌ Database connection failed: {e}")
            print("\n💡 Make sure:")
            print("   1. TimescaleDB is running (try: docker-compose up -d)")
            print("   2. Check your .env file configuration")
            print("   3. Verify network connectivity")
            return False
        
        print()
        
        # Step 2: Setup database schema
        print("🏗️  Step 2: Setting up database schema...")
        try:
            db_manager.create_tables()
            print("✅ Database schema created successfully!")
        except Exception as e:
            print(f"❌ Schema creation failed: {e}")
            return False
        
        print()
        
        # Step 3: Check for sample data and migrate
        sample_file = Path("sample_data.ndjson")
        if sample_file.exists():
            print("📥 Step 3: Migrating sample data...")
            try:
                migrator = NDJSONMigrator(batch_size=100)
                inserted_count = migrator.migrate_file(sample_file)
                print(f"✅ Successfully migrated {inserted_count} records!")
            except Exception as e:
                print(f"❌ Migration failed: {e}")
                return False
        else:
            print("⚠️  Step 3: No sample data found (sample_data.ndjson)")
            print("   You can create your own NDJSON files to migrate")
        
        print()
        
        # Step 4: Query and display results
        print("🔍 Step 4: Querying recent data...")
        try:
            # Get data from the last 7 days
            end_time = datetime.now()
            start_time = end_time - timedelta(days=7)
            
            results = db_manager.query_spectrum_data(
                start_time=start_time,
                end_time=end_time,
                limit=10
            )
            
            if results:
                print(f"✅ Found {len(results)} recent records:")
                print("-" * 80)
                
                for i, record in enumerate(results[:5], 1):  # Show first 5 records
                    print(f"Record {i}:")
                    print(f"  ID: {record['id']}")
                    print(f"  Time: {record['scan_time']}")
                    print(f"  Instance: {record['instance_name']}")
                    print(f"  Frequency: {record['cf']:,.0f} Hz")
                    print(f"  Span: {record['span']:,.0f} Hz")
                    print(f"  Samples: {record['sample_amount']}")
                    print("-" * 40)
                
                if len(results) > 5:
                    print(f"... and {len(results) - 5} more records")
                
            else:
                print("📭 No data found in the last 7 days")
                print("   Try migrating some NDJSON files first")
            
        except Exception as e:
            print(f"❌ Query failed: {e}")
            return False
        
        print()
        
        # Step 5: Display final statistics
        print("📊 Step 5: Final database statistics...")
        try:
            stats = db_manager.get_statistics()
            print("✅ Database Statistics:")
            for key, value in stats.items():
                if isinstance(value, datetime):
                    value = value.strftime("%Y-%m-%d %H:%M:%S UTC")
                print(f"   {key.replace('_', ' ').title()}: {value}")
        except Exception as e:
            print(f"❌ Failed to get statistics: {e}")
        
        print()
        print("=" * 60)
        print("🎉 Quick start completed successfully!")
        print("=" * 60)
        print()
        print("Next steps:")
        print("• Use 'python cli.py --help' to see all available commands")
        print("• Migrate your own NDJSON files with 'python cli.py migrate -i your_file.ndjson'")
        print("• Query data with filters using 'python cli.py query --help'")
        print("• Monitor with 'python cli.py stats'")
        print()
        
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("\n💡 Make sure you have:")
        print("   1. Activated the virtual environment")
        print("   2. Installed all dependencies: pip install -r requirements.txt")
        print("   3. Created and configured your .env file")
        return False
    
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        logger.exception("Quick start failed with unexpected error")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)