import numpy as np
from scipy import signal
from typing import List, Dict, Tuple, Optional
import json

class RFAnalysisTools:
    """RF Spectrum Analysis Tools"""
    
    @staticmethod
    def detect_peaks(powers: List[float], frequencies: List[float], 
                    threshold_dbm: float = -60, min_distance_mhz: float = 1.0,
                    prominence: float = 10) -> List[Dict]:
        """
        Detect peaks in RF spectrum data
        
        Args:
            powers: List of power values in dBm
            frequencies: List of frequency values in MHz
            threshold_dbm: Minimum power threshold for peak detection
            min_distance_mhz: Minimum distance between peaks in MHz
            prominence: Minimum prominence for peak detection
            
        Returns:
            List of detected peaks with frequency and power information
        """
        powers_array = np.array(powers)
        frequencies_array = np.array(frequencies)
        
        # Convert min_distance from MHz to samples
        freq_step = frequencies_array[1] - frequencies_array[0] if len(frequencies_array) > 1 else 1.0
        min_distance_samples = int(min_distance_mhz / freq_step)
        
        # Find peaks above threshold
        peak_indices, properties = signal.find_peaks(
            powers_array,
            height=threshold_dbm,
            distance=min_distance_samples,
            prominence=prominence
        )
        
        peaks = []
        for i, peak_idx in enumerate(peak_indices):
            peaks.append({
                'frequency_mhz': float(frequencies_array[peak_idx]),
                'power_dbm': float(powers_array[peak_idx]),
                'prominence': float(properties['prominences'][i]),
                'width': float(properties.get('widths', [0])[i]) * freq_step if 'widths' in properties else 0,
                'type': 'peak'
            })
        
        return sorted(peaks, key=lambda x: x['power_dbm'], reverse=True)
    
    @staticmethod
    def analyze_signal_statistics(powers: List[float], frequencies: List[float],
                                frequency_bands: Optional[List[Dict]] = None) -> Dict:
        """
        Calculate signal statistics for the spectrum
        
        Args:
            powers: List of power values in dBm
            frequencies: List of frequency values in MHz
            frequency_bands: Optional list of frequency bands to analyze
            
        Returns:
            Dictionary with signal statistics
        """
        powers_array = np.array(powers)
        frequencies_array = np.array(frequencies)
        
        stats = {
            'overall': {
                'max_power': float(np.max(powers_array)),
                'min_power': float(np.min(powers_array)),
                'mean_power': float(np.mean(powers_array)),
                'std_power': float(np.std(powers_array)),
                'median_power': float(np.median(powers_array)),
                'power_range': float(np.max(powers_array) - np.min(powers_array))
            },
            'frequency_range': {
                'start_mhz': float(frequencies_array[0]),
                'end_mhz': float(frequencies_array[-1]),
                'span_mhz': float(frequencies_array[-1] - frequencies_array[0]),
                'center_mhz': float((frequencies_array[0] + frequencies_array[-1]) / 2)
            }
        }
        
        # Analyze specific frequency bands if provided
        if frequency_bands:
            stats['bands'] = {}
            for band in frequency_bands:
                band_mask = (frequencies_array >= band['start']) & (frequencies_array <= band['end'])
                if np.any(band_mask):
                    band_powers = powers_array[band_mask]
                    stats['bands'][band['name']] = {
                        'max_power': float(np.max(band_powers)),
                        'min_power': float(np.min(band_powers)),
                        'mean_power': float(np.mean(band_powers)),
                        'std_power': float(np.std(band_powers)),
                        'band_start': band['start'],
                        'band_end': band['end']
                    }
        
        return stats
    
    @staticmethod
    def detect_interference(powers: List[float], frequencies: List[float],
                          baseline_window: int = 100, threshold_factor: float = 3) -> List[Dict]:
        """
        Detect potential interference sources
        
        Args:
            powers: List of power values in dBm
            frequencies: List of frequency values in MHz
            baseline_window: Window size for baseline calculation
            threshold_factor: Factor above baseline to consider interference
            
        Returns:
            List of potential interference sources
        """
        powers_array = np.array(powers)
        frequencies_array = np.array(frequencies)
        
        # Calculate rolling baseline
        baseline = np.convolve(powers_array, np.ones(baseline_window)/baseline_window, mode='same')
        baseline_std = np.convolve(np.abs(powers_array - baseline), 
                                 np.ones(baseline_window)/baseline_window, mode='same')
        
        # Find points significantly above baseline
        threshold = baseline + threshold_factor * baseline_std
        interference_mask = powers_array > threshold
        
        # Group consecutive interference points
        interference_regions = []
        in_region = False
        region_start = None
        
        for i, is_interference in enumerate(interference_mask):
            if is_interference and not in_region:
                # Start of new region
                in_region = True
                region_start = i
            elif not is_interference and in_region:
                # End of region
                in_region = False
                region_end = i - 1
                
                # Calculate region properties
                region_powers = powers_array[region_start:region_end+1]
                region_frequencies = frequencies_array[region_start:region_end+1]
                
                interference_regions.append({
                    'start_frequency_mhz': float(region_frequencies[0]),
                    'end_frequency_mhz': float(region_frequencies[-1]),
                    'center_frequency_mhz': float(np.mean(region_frequencies)),
                    'max_power_dbm': float(np.max(region_powers)),
                    'mean_power_dbm': float(np.mean(region_powers)),
                    'bandwidth_mhz': float(region_frequencies[-1] - region_frequencies[0]),
                    'type': 'interference'
                })
        
        # Handle case where interference extends to end of spectrum
        if in_region:
            region_powers = powers_array[region_start:]
            region_frequencies = frequencies_array[region_start:]
            
            interference_regions.append({
                'start_frequency_mhz': float(region_frequencies[0]),
                'end_frequency_mhz': float(region_frequencies[-1]),
                'center_frequency_mhz': float(np.mean(region_frequencies)),
                'max_power_dbm': float(np.max(region_powers)),
                'mean_power_dbm': float(np.mean(region_powers)),
                'bandwidth_mhz': float(region_frequencies[-1] - region_frequencies[0]),
                'type': 'interference'
            })
        
        return sorted(interference_regions, key=lambda x: x['max_power_dbm'], reverse=True)
    
    @staticmethod
    def apply_analysis_preset(powers: List[float], frequencies: List[float], 
                            preset_config: Dict) -> Dict:
        """
        Apply an analysis preset to spectrum data
        
        Args:
            powers: List of power values in dBm
            frequencies: List of frequency values in MHz
            preset_config: Configuration dictionary for the analysis
            
        Returns:
            Analysis results based on the preset type
        """
        analysis_type = preset_config.get('type', 'unknown')
        
        if analysis_type == 'peak_detection':
            return {
                'type': 'peak_detection',
                'results': RFAnalysisTools.detect_peaks(
                    powers, frequencies,
                    threshold_dbm=preset_config.get('threshold_dbm', -60),
                    min_distance_mhz=preset_config.get('min_distance_mhz', 1.0),
                    prominence=preset_config.get('prominence', 10)
                )
            }
        
        elif analysis_type == 'signal_analysis':
            return {
                'type': 'signal_analysis',
                'results': RFAnalysisTools.analyze_signal_statistics(
                    powers, frequencies,
                    frequency_bands=preset_config.get('frequency_bands')
                )
            }
        
        elif analysis_type == 'interference':
            return {
                'type': 'interference',
                'results': RFAnalysisTools.detect_interference(
                    powers, frequencies,
                    baseline_window=preset_config.get('baseline_window', 100),
                    threshold_factor=preset_config.get('threshold_factor', 3)
                )
            }
        
        else:
            return {
                'type': 'unknown',
                'error': f'Unknown analysis type: {analysis_type}'
            }
    
    @staticmethod
    def calculate_frequency_axis(center_frequency: float, span: float, num_points: int) -> List[float]:
        """
        Calculate frequency axis for spectrum data
        
        Args:
            center_frequency: Center frequency in MHz
            span: Frequency span in MHz
            num_points: Number of frequency points
            
        Returns:
            List of frequency values in MHz
        """
        start_freq = center_frequency - span / 2
        end_freq = center_frequency + span / 2
        return np.linspace(start_freq, end_freq, num_points).tolist()