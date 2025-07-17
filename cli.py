import click
from datetime import datetime, timedelta
from typing import Optional
import json
from pathlib import Path

from database import db_manager
from models import SpectrumData, ConfigInfo
from ndjson_migrator import NDJSONMigrator

@click.group()
def cli():
    """TimescaleDB Spectrum Data Management CLI"""
    pass

@cli.command()
def setup():
    """Setup TimescaleDB tables and hypertables"""
    try:
        click.echo("Setting up TimescaleDB tables...")
        db_manager.create_tables()
        click.echo("✅ Database setup completed successfully!")
    except Exception as e:
        click.echo(f"❌ Database setup failed: {e}", err=True)

@cli.command()
def stats():
    """Show database statistics"""
    try:
        click.echo("Fetching database statistics...")
        stats = db_manager.get_statistics()
        
        click.echo("\n📊 Database Statistics:")
        click.echo("─" * 40)
        for key, value in stats.items():
            if isinstance(value, datetime):
                value = value.strftime("%Y-%m-%d %H:%M:%S UTC")
            click.echo(f"  {key.replace('_', ' ').title()}: {value}")
            
    except Exception as e:
        click.echo(f"❌ Failed to get statistics: {e}", err=True)

@cli.command()
@click.option('--input-path', '-i', required=True, 
              help='Path to NDJSON file or directory')
@click.option('--batch-size', '-b', default=1000, 
              help='Batch size for processing')
@click.option('--pattern', '-p', default="*.ndjson", 
              help='File pattern for directory processing')
def migrate(input_path: str, batch_size: int, pattern: str):
    """Migrate NDJSON files to TimescaleDB"""
    
    input_path = Path(input_path)
    
    if not input_path.exists():
        click.echo(f"❌ Path {input_path} does not exist", err=True)
        return
    
    migrator = NDJSONMigrator(batch_size=batch_size)
    
    try:
        if input_path.is_file():
            click.echo(f"🔄 Migrating file: {input_path}")
            total_inserted = migrator.migrate_file(input_path)
        else:
            click.echo(f"🔄 Migrating directory: {input_path}")
            total_inserted = migrator.migrate_directory(input_path, pattern)
        
        click.echo(f"✅ Migration completed! Records inserted: {total_inserted}")
        
    except Exception as e:
        click.echo(f"❌ Migration failed: {e}", err=True)

@cli.command()
@click.option('--start-time', '-s', help='Start time (YYYY-MM-DD HH:MM:SS)')
@click.option('--end-time', '-e', help='End time (YYYY-MM-DD HH:MM:SS)')
@click.option('--instance', '-inst', help='Instance name filter')
@click.option('--limit', '-l', default=10, help='Number of records to show')
@click.option('--output', '-o', help='Output file (JSON format)')
def query(start_time: Optional[str], end_time: Optional[str], 
          instance: Optional[str], limit: int, output: Optional[str]):
    """Query spectrum data with optional filters"""
    
    try:
        # Parse datetime strings
        start_dt = None
        end_dt = None
        
        if start_time:
            start_dt = datetime.strptime(start_time, "%Y-%m-%d %H:%M:%S")
        
        if end_time:
            end_dt = datetime.strptime(end_time, "%Y-%m-%d %H:%M:%S")
        
        click.echo("🔍 Querying spectrum data...")
        results = db_manager.query_spectrum_data(
            start_time=start_dt,
            end_time=end_dt,
            instance_name=instance,
            limit=limit
        )
        
        if not results:
            click.echo("📭 No data found matching the criteria")
            return
        
        if output:
            # Save to file
            output_path = Path(output)
            with open(output_path, 'w') as f:
                json.dump(results, f, indent=2, default=str)
            click.echo(f"💾 Results saved to {output_path}")
        else:
            # Display in console
            click.echo(f"\n📋 Found {len(results)} records:")
            click.echo("─" * 80)
            
            for i, record in enumerate(results):
                click.echo(f"Record {i+1}:")
                click.echo(f"  ID: {record['id']}")
                click.echo(f"  Scan Time: {record['scan_time']}")
                click.echo(f"  Instance: {record['instance_name']}")
                click.echo(f"  CF: {record['cf']} Hz")
                click.echo(f"  Span: {record['span']} Hz")
                click.echo(f"  Samples: {record['sample_amount']}")
                if record['config_extra']:
                    click.echo(f"  Extra Config: {record['config_extra']}")
                click.echo("─" * 40)
                
    except ValueError as e:
        click.echo(f"❌ Invalid datetime format. Use YYYY-MM-DD HH:MM:SS", err=True)
    except Exception as e:
        click.echo(f"❌ Query failed: {e}", err=True)

@cli.command()
@click.option('--days', '-d', default=7, help='Number of recent days to show')
@click.option('--instance', '-inst', help='Instance name filter')
def recent(days: int, instance: Optional[str]):
    """Show recent spectrum data"""
    
    try:
        end_time = datetime.now()
        start_time = end_time - timedelta(days=days)
        
        click.echo(f"🕒 Showing data from last {days} days...")
        
        results = db_manager.query_spectrum_data(
            start_time=start_time,
            end_time=end_time,
            instance_name=instance,
            limit=50
        )
        
        if not results:
            click.echo("📭 No recent data found")
            return
        
        click.echo(f"\n📊 Found {len(results)} recent records:")
        click.echo("─" * 60)
        
        for record in results:
            click.echo(f"{record['scan_time']} | {record['instance_name']} | ID: {record['id']}")
            
    except Exception as e:
        click.echo(f"❌ Failed to get recent data: {e}", err=True)

@cli.command()
def test_connection():
    """Test database connection"""
    try:
        click.echo("🔗 Testing database connection...")
        stats = db_manager.get_statistics()
        click.echo("✅ Database connection successful!")
        click.echo(f"   Total records: {stats.get('total_records', 0)}")
    except Exception as e:
        click.echo(f"❌ Database connection failed: {e}", err=True)
        click.echo("\n💡 Make sure:")
        click.echo("   1. TimescaleDB is running")
        click.echo("   2. Database credentials are correct in .env file")
        click.echo("   3. Database name exists")
        click.echo("   4. Network connectivity is available")

if __name__ == '__main__':
    cli()