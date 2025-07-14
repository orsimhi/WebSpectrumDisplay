import json
import logging
from pathlib import Path
from typing import List, Generator, Dict, Any
from tqdm import tqdm
import click

from models import SpectrumData, ConfigInfo
from database import db_manager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class NDJSONMigrator:
    """Migrates NDJSON files to TimescaleDB"""
    
    def __init__(self, batch_size: int = 1000):
        self.batch_size = batch_size
    
    def read_ndjson_file(self, file_path: Path) -> Generator[Dict[str, Any], None, None]:
        """Read NDJSON file line by line"""
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                for line_num, line in enumerate(file, 1):
                    line = line.strip()
                    if not line:
                        continue
                    
                    try:
                        yield json.loads(line)
                    except json.JSONDecodeError as e:
                        logger.warning(f"Invalid JSON on line {line_num} in {file_path}: {e}")
                        continue
                        
        except FileNotFoundError:
            logger.error(f"File not found: {file_path}")
            raise
        except Exception as e:
            logger.error(f"Error reading file {file_path}: {e}")
            raise
    
    def parse_spectrum_data(self, raw_data: Dict[str, Any]) -> SpectrumData:
        """Parse raw data into SpectrumData model"""
        try:
            # Handle config_info field
            config_info_raw = raw_data.get('config_info', {})
            
            # Create ConfigInfo object
            config_info = ConfigInfo(**config_info_raw)
            
            # Create SpectrumData object
            spectrum_data = SpectrumData(
                scan_time=raw_data['scan_time'],
                id=raw_data['id'],
                instance_name=raw_data.get('instance_name', 'unknown'),
                config_info=config_info
            )
            
            return spectrum_data
            
        except Exception as e:
            logger.error(f"Error parsing spectrum data: {e}, Data: {raw_data}")
            raise
    
    def migrate_file(self, file_path: Path) -> int:
        """Migrate single NDJSON file to TimescaleDB"""
        logger.info(f"Starting migration of file: {file_path}")
        
        total_processed = 0
        total_inserted = 0
        batch = []
        
        try:
            # Count total lines for progress bar
            total_lines = sum(1 for line in open(file_path, 'r', encoding='utf-8') if line.strip())
            
            with tqdm(total=total_lines, desc=f"Migrating {file_path.name}") as pbar:
                for raw_data in self.read_ndjson_file(file_path):
                    try:
                        spectrum_data = self.parse_spectrum_data(raw_data)
                        batch.append(spectrum_data)
                        total_processed += 1
                        
                        # Process batch when it reaches batch_size
                        if len(batch) >= self.batch_size:
                            inserted = db_manager.insert_spectrum_data(batch)
                            total_inserted += inserted
                            batch = []
                            
                    except Exception as e:
                        logger.warning(f"Skipping invalid record: {e}")
                    
                    pbar.update(1)
                
                # Process remaining batch
                if batch:
                    inserted = db_manager.insert_spectrum_data(batch)
                    total_inserted += inserted
            
            logger.info(f"Migration completed. Processed: {total_processed}, Inserted: {total_inserted}")
            return total_inserted
            
        except Exception as e:
            logger.error(f"Migration failed for file {file_path}: {e}")
            raise
    
    def migrate_directory(self, directory_path: Path, pattern: str = "*.ndjson") -> int:
        """Migrate all NDJSON files in a directory"""
        logger.info(f"Starting migration of directory: {directory_path}")
        
        ndjson_files = list(directory_path.glob(pattern))
        if not ndjson_files:
            logger.warning(f"No NDJSON files found in {directory_path} with pattern {pattern}")
            return 0
        
        total_inserted = 0
        
        for file_path in ndjson_files:
            try:
                inserted = self.migrate_file(file_path)
                total_inserted += inserted
            except Exception as e:
                logger.error(f"Failed to migrate {file_path}: {e}")
                continue
        
        logger.info(f"Directory migration completed. Total inserted: {total_inserted}")
        return total_inserted

@click.command()
@click.option('--input-path', '-i', required=True, 
              help='Path to NDJSON file or directory containing NDJSON files')
@click.option('--batch-size', '-b', default=1000, 
              help='Number of records to process in each batch')
@click.option('--pattern', '-p', default="*.ndjson", 
              help='File pattern to match when input is a directory')
@click.option('--setup-db', is_flag=True, 
              help='Setup database tables before migration')
def migrate_ndjson(input_path: str, batch_size: int, pattern: str, setup_db: bool):
    """Migrate NDJSON files to TimescaleDB"""
    
    input_path = Path(input_path)
    
    if not input_path.exists():
        click.echo(f"Error: Path {input_path} does not exist", err=True)
        return
    
    # Setup database if requested
    if setup_db:
        click.echo("Setting up database tables...")
        try:
            db_manager.create_tables()
            click.echo("Database setup completed successfully")
        except Exception as e:
            click.echo(f"Database setup failed: {e}", err=True)
            return
    
    # Initialize migrator
    migrator = NDJSONMigrator(batch_size=batch_size)
    
    try:
        if input_path.is_file():
            # Migrate single file
            total_inserted = migrator.migrate_file(input_path)
        else:
            # Migrate directory
            total_inserted = migrator.migrate_directory(input_path, pattern)
        
        click.echo(f"Migration completed successfully. Total records inserted: {total_inserted}")
        
        # Show statistics
        stats = db_manager.get_statistics()
        click.echo("\nDatabase Statistics:")
        for key, value in stats.items():
            click.echo(f"  {key}: {value}")
            
    except Exception as e:
        click.echo(f"Migration failed: {e}", err=True)

if __name__ == "__main__":
    migrate_ndjson()