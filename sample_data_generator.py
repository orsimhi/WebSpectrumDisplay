#!/usr/bin/env python3
"""
Sample RF Spectrum Data Generator for TimescaleDB

This script generates realistic RF spectrum data and inserts it into the database.
It creates data for various spectrum analyzer configurations and use cases.

Windows Compatible Version
"""

import os
import sys
import random
import uuid
import numpy as np
import logging
from datetime import datetime, timezone, timedelta
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Add the current directory to the path to import our models
current_dir = Path(__file__).parent.absolute()
sys.path.append(str(current_dir))

from models import RFScan, AnalysisPreset, ScanMarker
from analysis_tools import RFAnalysisTools

# Database configuration
DATABASE_URL = os.environ.get(
    'DATABASE_URL', 
    'postgresql://rf_user:rf_password_123@localhost:5432/rf_spectrum_db'
)

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('logs/data_generator.log', encoding='utf-8') if Path('logs').exists() else logging.NullHandler()
    ]
)
logger = logging.getLogger(__name__)

def create_database_session():
    """Create database engine and session"""
    try:
        engine = create_engine(DATABASE_URL, echo=False)
        Session = sessionmaker(bind=engine)
        return Session()
    except Exception as e:
        logger.error(f"Failed to create database session: {e}")
        raise

def generate_realistic_spectrum(center_freq, span, num_points, config_name):
    """Generate realistic RF spectrum data based on configuration"""
    
    # Calculate frequency axis
    frequencies = RFAnalysisTools.calculate_frequency_axis(center_freq, span, num_points)
    
    # Start with noise floor
    noise_floor = -85 + 3 * np.random.randn(num_points)
    powers = noise_floor.copy()
    
    # Add signals based on configuration type
    if "WiFi" in config_name or "2.4G" in config_name:
        # Add WiFi channels (2.4 GHz band)
        wifi_channels = [2412, 2417, 2422, 2427, 2432, 2437, 2442, 2447, 2452, 2457, 2462]
        for channel_freq in wifi_channels:
            if center_freq - span/2 <= channel_freq <= center_freq + span/2:
                # Find index for this frequency
                freq_idx = int((channel_freq - frequencies[0]) / (frequencies[1] - frequencies[0]))
                if 0 <= freq_idx < num_points:
                    # Add WiFi signal with some variability
                    signal_power = random.uniform(-70, -40)
                    bandwidth_points = int(20 / (frequencies[1] - frequencies[0]))  # ~20 MHz bandwidth
                    
                    for i in range(max(0, freq_idx - bandwidth_points//2), 
                                 min(num_points, freq_idx + bandwidth_points//2)):
                        distance_from_center = abs(i - freq_idx)
                        rolloff = max(0, signal_power - distance_from_center * 0.5)
                        powers[i] = max(powers[i], rolloff)
    
    elif "Bluetooth" in config_name:
        # Add Bluetooth frequency hopping signals
        for _ in range(random.randint(3, 8)):
            hop_freq = random.uniform(center_freq - span/3, center_freq + span/3)
            freq_idx = int((hop_freq - frequencies[0]) / (frequencies[1] - frequencies[0]))
            if 0 <= freq_idx < num_points:
                signal_power = random.uniform(-60, -30)
                bandwidth_points = int(1 / (frequencies[1] - frequencies[0]))  # ~1 MHz bandwidth
                
                for i in range(max(0, freq_idx - bandwidth_points//2), 
                             min(num_points, freq_idx + bandwidth_points//2)):
                    distance_from_center = abs(i - freq_idx)
                    rolloff = max(0, signal_power - distance_from_center * 2)
                    powers[i] = max(powers[i], rolloff)
    
    elif "Cellular" in config_name or "LTE" in config_name:
        # Add cellular/LTE signals
        for _ in range(random.randint(1, 3)):
            signal_freq = random.uniform(center_freq - span/3, center_freq + span/3)
            freq_idx = int((signal_freq - frequencies[0]) / (frequencies[1] - frequencies[0]))
            if 0 <= freq_idx < num_points:
                signal_power = random.uniform(-50, -20)
                bandwidth_points = int(random.choice([5, 10, 15, 20]) / (frequencies[1] - frequencies[0]))
                
                for i in range(max(0, freq_idx - bandwidth_points//2), 
                             min(num_points, freq_idx + bandwidth_points//2)):
                    distance_from_center = abs(i - freq_idx)
                    rolloff = max(0, signal_power - distance_from_center * 0.3)
                    powers[i] = max(powers[i], rolloff)
    
    elif "FM" in config_name:
        # Add FM radio signals
        fm_frequencies = list(range(int(center_freq - span/2), int(center_freq + span/2), 2))  # Every 200 kHz
        for fm_freq in fm_frequencies:
            if random.random() < 0.3:  # 30% chance of signal
                freq_idx = int((fm_freq - frequencies[0]) / (frequencies[1] - frequencies[0]))
                if 0 <= freq_idx < num_points:
                    signal_power = random.uniform(-60, -30)
                    bandwidth_points = int(0.2 / (frequencies[1] - frequencies[0]))  # 200 kHz bandwidth
                    
                    for i in range(max(0, freq_idx - bandwidth_points//2), 
                                 min(num_points, freq_idx + bandwidth_points//2)):
                        distance_from_center = abs(i - freq_idx)
                        rolloff = max(0, signal_power - distance_from_center * 1)
                        powers[i] = max(powers[i], rolloff)
    
    else:
        # Generic signals for other configurations
        num_signals = random.randint(1, 5)
        for _ in range(num_signals):
            signal_freq = random.uniform(center_freq - span/3, center_freq + span/3)
            freq_idx = int((signal_freq - frequencies[0]) / (frequencies[1] - frequencies[0]))
            if 0 <= freq_idx < num_points:
                signal_power = random.uniform(-70, -20)
                bandwidth_points = random.randint(5, 50)
                
                for i in range(max(0, freq_idx - bandwidth_points//2), 
                             min(num_points, freq_idx + bandwidth_points//2)):
                    distance_from_center = abs(i - freq_idx)
                    rolloff = max(0, signal_power - distance_from_center * 0.5)
                    powers[i] = max(powers[i], rolloff)
    
    return powers.tolist()

def generate_sample_data(session, num_scans=100):
    """Generate sample RF spectrum data"""
    
    logger.info(f"Generating {num_scans} sample RF scans...")
    
    # Configuration templates
    configs = [
        # WiFi and ISM band analysis
        {"name": "WiFi_Ch1_Survey", "cf": 2412.0, "span": 20.0, "sample_amount": 1000, "rbw": 0.1, "vbw": 0.3, "ref_level": -30},
        {"name": "WiFi_Ch6_Survey", "cf": 2437.0, "span": 20.0, "sample_amount": 1000, "rbw": 0.1, "vbw": 0.3, "ref_level": -30},
        {"name": "WiFi_Ch11_Survey", "cf": 2462.0, "span": 20.0, "sample_amount": 1000, "rbw": 0.1, "vbw": 0.3, "ref_level": -30},
        {"name": "ISM_2.4G_Wideband", "cf": 2450.0, "span": 100.0, "sample_amount": 2000, "rbw": 1.0, "vbw": 1.0, "ref_level": -40},
        {"name": "Bluetooth_Analysis", "cf": 2440.0, "span": 80.0, "sample_amount": 1600, "rbw": 1.0, "vbw": 3.0, "ref_level": -35},
        
        # 5 GHz WiFi
        {"name": "WiFi_5G_Ch36", "cf": 5180.0, "span": 20.0, "sample_amount": 1000, "rbw": 0.1, "vbw": 0.3, "ref_level": -30},
        {"name": "WiFi_5G_Ch44", "cf": 5220.0, "span": 20.0, "sample_amount": 1000, "rbw": 0.1, "vbw": 0.3, "ref_level": -30},
        {"name": "WiFi_5G_Wideband", "cf": 5250.0, "span": 200.0, "sample_amount": 2000, "rbw": 1.0, "vbw": 1.0, "ref_level": -40},
        
        # Cellular bands
        {"name": "LTE_Band7_DL", "cf": 2655.0, "span": 70.0, "sample_amount": 1400, "rbw": 1.0, "vbw": 1.0, "ref_level": -25},
        {"name": "LTE_Band3_UL", "cf": 1747.5, "span": 75.0, "sample_amount": 1500, "rbw": 1.0, "vbw": 1.0, "ref_level": -25},
        {"name": "Cellular_850", "cf": 850.0, "span": 50.0, "sample_amount": 1000, "rbw": 1.0, "vbw": 3.0, "ref_level": -30},
        
        # FM Radio
        {"name": "FM_Radio_Band", "cf": 100.0, "span": 20.0, "sample_amount": 2000, "rbw": 0.01, "vbw": 0.03, "ref_level": -20},
        
        # Other bands
        {"name": "GPS_L1_Survey", "cf": 1575.42, "span": 20.0, "sample_amount": 1000, "rbw": 0.1, "vbw": 0.1, "ref_level": -50},
        {"name": "UHF_TV_Band", "cf": 600.0, "span": 100.0, "sample_amount": 2000, "rbw": 1.0, "vbw": 3.0, "ref_level": -30},
        {"name": "Amateur_2m", "cf": 145.0, "span": 4.0, "sample_amount": 800, "rbw": 0.01, "vbw": 0.03, "ref_level": -40},
    ]
    
    # Instance names (different analyzer units)
    instance_names = [
        "SA_Lab_001", "SA_Lab_002", "SA_Mobile_Alpha", "SA_Mobile_Beta", 
        "SA_Remote_001", "Portable_Analyzer_A", "Portable_Analyzer_B",
        "Base_Station_SA", "Field_Unit_1", "Field_Unit_2"
    ]
    
    # Generate scan data over the last week
    end_time = datetime.now(timezone.utc)
    start_time = end_time - timedelta(days=7)
    
    scans_created = 0
    markers_created = 0
    
    try:
        for i in range(num_scans):
            # Random timestamp within the last week
            time_offset = random.uniform(0, (end_time - start_time).total_seconds())
            scan_time = start_time + timedelta(seconds=time_offset)
            
            # Select random configuration
            config = random.choice(configs).copy()
            
            # Add some frequency variation
            config["cf"] += random.uniform(-config["span"] * 0.1, config["span"] * 0.1)
            
            # Generate RF spectrum data
            powers = generate_realistic_spectrum(
                config["cf"], config["span"], config["sample_amount"], config["name"]
            )
            
            # Create flags based on signal characteristics
            flags = []
            max_power = max(powers)
            if max_power > -30:
                flags.append("high_signal")
            if max_power > -40:
                flags.append("signal_detected")
            if len([p for p in powers if p > -50]) > config["sample_amount"] * 0.1:
                flags.append("interference_possible")
            
            # Create RF scan record
            scan = RFScan(
                scan_time=scan_time,
                scan_id=uuid.uuid4(),
                flags=flags,
                instance_name=random.choice(instance_names),
                powers=powers,
                config_info=config
            )
            
            session.add(scan)
            scans_created += 1
            
            # Add markers for some scans (30% chance)
            if random.random() < 0.3:
                # Generate frequency axis for peak detection
                frequencies = RFAnalysisTools.calculate_frequency_axis(
                    config["cf"], config["span"], len(powers)
                )
                
                # Detect peaks automatically
                try:
                    detected_peaks = RFAnalysisTools.detect_peaks(
                        powers, frequencies, threshold_dbm=-70, min_distance_mhz=1.0
                    )
                    
                    # Add markers for top peaks (up to 3)
                    for j, peak in enumerate(detected_peaks[:3]):
                        marker_name = f"Peak_{j+1}"
                        if peak['power_dbm'] > -40:
                            marker_name = f"Strong_Signal_{j+1}"
                        elif peak['power_dbm'] > -60:
                            marker_name = f"Medium_Signal_{j+1}"
                        
                        marker = ScanMarker(
                            scan_time=scan_time,
                            scan_id=scan.scan_id,
                            marker_name=marker_name,
                            frequency_mhz=peak['frequency_mhz'],
                            power_dbm=peak['power_dbm'],
                            marker_type='peak',
                            notes=f"Auto-detected peak with {peak['prominence']:.1f} dB prominence"
                        )
                        session.add(marker)
                        markers_created += 1
                        
                except Exception as e:
                    logger.warning(f"Could not create markers for scan {i}: {e}")
            
            # Commit every 10 scans to avoid memory issues
            if (i + 1) % 10 == 0:
                try:
                    session.commit()
                    logger.info(f"Created {i + 1}/{num_scans} scans...")
                except Exception as e:
                    logger.error(f"Error committing batch: {e}")
                    session.rollback()
                    raise
        
        # Final commit
        session.commit()
        logger.info(f"✓ Created {scans_created} RF scans and {markers_created} markers")
        
    except Exception as e:
        logger.error(f"Error generating sample data: {e}")
        session.rollback()
        raise

def main():
    """Main function"""
    print("RF Spectrum Data Generator for TimescaleDB (Windows Version)")
    print("=" * 60)
    
    # Get number of scans to generate
    num_scans = 200
    if len(sys.argv) > 1:
        try:
            num_scans = int(sys.argv[1])
            if num_scans <= 0:
                raise ValueError("Number of scans must be positive")
        except ValueError as e:
            print(f"Invalid number of scans: {e}. Using default: 200")
            num_scans = 200
    
    print(f"Generating {num_scans} sample scans...")
    
    try:
        # Create database session
        logger.info("Connecting to database...")
        session = create_database_session()
        
        # Check if database is accessible
        from sqlalchemy import text
        session.execute(text('SELECT 1'))
        logger.info("✓ Database connection successful")
        
        # Generate sample data
        generate_sample_data(session, num_scans)
        
        print("\n" + "=" * 60)
        print("         Sample Data Generation Complete!")
        print("=" * 60)
        print(f"\nGenerated {num_scans} RF spectrum scans with markers")
        print("\nYou can now run the RF Spectrum Analyzer application:")
        print("  - Docker: run setup.bat")
        print("  - Local: run run_app.bat")
        print("\nAccess the application at: http://localhost:5000")
        
    except Exception as e:
        logger.error(f"✗ Error: {e}")
        print(f"\nError: {e}")
        print("\nTroubleshooting:")
        print("  1. Make sure TimescaleDB is running")
        print("  2. Check database connection settings")
        print("  3. Ensure Python dependencies are installed")
        print("  4. Run setup_dev.bat to set up the environment")
        
        input("\nPress Enter to exit...")
        sys.exit(1)
    
    finally:
        if 'session' in locals():
            session.close()

if __name__ == "__main__":
    main()