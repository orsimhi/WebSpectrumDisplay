class RFSpectrumAnalyzer {
    constructor() {
        this.scans = [];
        this.currentScanIndex = 0;
        this.currentPage = 1;
        this.totalPages = 1;
        this.totalScans = 0;
        this.perPage = 20;
        this.markers = [];
        this.isPlaying = false;
        this.playInterval = null;
        this.socket = null;
        this.currentScan = null;
        this.markerCounter = 1;
        this.filters = {
            cf: '',
            name: '',
            instance: '',
            timeRange: '24h'
        };
        this.analysisPresets = [];
        this.pendingMarker = null;
        
        this.init();
    }

    async init() {
        this.initializeWebSocket();
        await this.loadAnalysisPresets();
        await this.loadScans();
        this.setupEventListeners();
        if (this.scans.length > 0) {
            await this.displayScan(0);
        }
        this.hideLoading();
    }

    initializeWebSocket() {
        try {
            this.socket = io();
            
            this.socket.on('connect', () => {
                console.log('Connected to WebSocket server');
                this.showStatus('Connected to real-time updates', 'success');
            });

            this.socket.on('disconnect', () => {
                console.log('Disconnected from WebSocket server');
                this.showStatus('Disconnected from real-time updates', 'warning');
            });

            this.socket.on('latest_scan_update', (data) => {
                this.showStatus(`New scan: ${data.config_name} from ${data.instance_name}`, 'info');
            });

            this.socket.on('navigation_result', (data) => {
                this.navigateToScan(data.scan_id);
            });

            this.socket.on('navigation_error', (data) => {
                this.showStatus(data.msg, 'warning');
            });

        } catch (error) {
            console.warn('WebSocket not available:', error);
            this.showStatus('Real-time updates not available', 'warning');
        }
    }

    async loadAnalysisPresets() {
        try {
            const response = await fetch('/api/analysis/presets');
            const presets = await response.json();
            
            this.analysisPresets = presets;
            this.updateAnalysisPresetOptions();
            
        } catch (error) {
            console.error('Error loading analysis presets:', error);
        }
    }

    updateAnalysisPresetOptions() {
        const select = document.getElementById('analysis-preset');
        select.innerHTML = '<option value="">Select Analysis...</option>';
        
        this.analysisPresets.forEach(preset => {
            const option = document.createElement('option');
            option.value = preset.id;
            option.textContent = preset.name;
            option.title = preset.description;
            select.appendChild(option);
        });
    }

    async loadScans(page = 1) {
        try {
            this.showLoading();
            
            const params = new URLSearchParams({
                page: page,
                per_page: this.perPage
            });

            // Add filters if they exist
            if (this.filters.cf) params.append('cf', this.filters.cf);
            if (this.filters.name) params.append('name', this.filters.name);
            if (this.filters.instance) params.append('instance', this.filters.instance);
            
            // Add time range filter
            if (this.filters.timeRange) {
                const now = new Date();
                let startTime;
                
                switch (this.filters.timeRange) {
                    case '1h':
                        startTime = new Date(now.getTime() - 60 * 60 * 1000);
                        break;
                    case '6h':
                        startTime = new Date(now.getTime() - 6 * 60 * 60 * 1000);
                        break;
                    case '24h':
                        startTime = new Date(now.getTime() - 24 * 60 * 60 * 1000);
                        break;
                    case '7d':
                        startTime = new Date(now.getTime() - 7 * 24 * 60 * 60 * 1000);
                        break;
                }
                
                if (startTime) {
                    params.append('start_time', startTime.toISOString());
                }
            }

            const response = await fetch(`/api/scans?${params}`);
            const result = await response.json();
            
            if (result.error) {
                throw new Error(result.error);
            }

            this.scans = result.scans;
            this.currentPage = result.page;
            this.totalPages = result.pages;
            this.totalScans = result.total;
            this.hasNext = result.has_next;
            this.hasPrev = result.has_prev;
            
            this.updateInfo();
            this.updatePaginationButtons();
            
        } catch (error) {
            console.error('Error loading RF scans:', error);
            this.showStatus('Error loading data: ' + error.message, 'error');
        } finally {
            this.hideLoading();
        }
    }

    async navigateToScan(scanId) {
        // Find scan in current data
        const scanIndex = this.scans.findIndex(scan => scan.scan_id === scanId);
        if (scanIndex >= 0) {
            await this.displayScan(scanIndex);
        } else {
            // Scan not in current page, need to load it
            try {
                const response = await fetch(`/api/scans/${scanId}`);
                const scan = await response.json();
                
                if (!scan.error) {
                    // Add to current scans and display
                    this.scans.unshift(scan);
                    await this.displayScan(0);
                }
            } catch (error) {
                console.error('Error loading scan:', error);
            }
        }
    }

    async displayScan(index) {
        if (index < 0 || index >= this.scans.length) return;
        
        this.currentScanIndex = index;
        this.currentScan = this.scans[index];
        
        try {
            const response = await fetch(`/api/plot/${this.currentScan.scan_id}`);
            const plotData = await response.json();
            
            if (plotData.error) {
                throw new Error(plotData.error);
            }

            // Parse and display the plot
            const plotConfig = JSON.parse(plotData.plot);
            const plotDiv = document.getElementById('rf-plot');
            
            await Plotly.newPlot(plotDiv, plotConfig.data, plotConfig.layout, {
                responsive: true,
                displayModeBar: true,
                modeBarButtonsToRemove: ['pan2d', 'lasso2d'],
            });

            // Add click event for marker placement
            plotDiv.on('plotly_click', (data) => {
                if (data.points && data.points.length > 0) {
                    const point = data.points[0];
                    this.openMarkerDialog(point.x, point.y);
                }
            });

            // Update info display
            this.updateScanInfo();
            this.loadScanMarkers();
            
        } catch (error) {
            console.error('Error displaying scan:', error);
            this.showStatus('Error displaying scan: ' + error.message, 'error');
        }
    }

    async loadScanMarkers() {
        if (!this.currentScan) return;
        
        // Markers are already included in the scan data
        this.markers = this.currentScan.markers || [];
        this.updateMarkersDisplay();
    }

    setupEventListeners() {
        // Filter controls
        document.getElementById('apply-filters-btn').addEventListener('click', () => this.applyFilters());
        document.getElementById('clear-filters-btn').addEventListener('click', () => this.clearFilters());

        // Navigation buttons
        document.getElementById('first-btn').addEventListener('click', () => this.goToFirst());
        document.getElementById('prev-btn').addEventListener('click', () => this.goToPrevious());
        document.getElementById('next-btn').addEventListener('click', () => this.goToNext());
        document.getElementById('last-btn').addEventListener('click', () => this.goToLast());
        document.getElementById('play-btn').addEventListener('click', () => this.toggleAutoPlay());

        // Pagination buttons
        document.getElementById('prev-page-btn').addEventListener('click', () => this.prevPage());
        document.getElementById('next-page-btn').addEventListener('click', () => this.nextPage());

        // Analysis tools
        document.getElementById('apply-analysis-btn').addEventListener('click', () => this.applyAnalysis());
        document.getElementById('add-marker-btn').addEventListener('click', () => this.showAddMarkerHelp());
        document.getElementById('clear-markers-btn').addEventListener('click', () => this.clearMarkers());
        document.getElementById('reset-zoom-btn').addEventListener('click', () => this.resetZoom());

        // Keyboard shortcuts
        document.addEventListener('keydown', (e) => this.handleKeyboard(e));

        // Speed control
        document.getElementById('playback-speed').addEventListener('change', (e) => {
            if (this.isPlaying) {
                this.stopAutoPlay();
                this.startAutoPlay();
            }
        });
    }

    handleKeyboard(e) {
        // Don't handle keys when typing in inputs
        if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA' || e.target.tagName === 'SELECT') {
            return;
        }

        switch(e.key) {
            case 'ArrowLeft':
                e.preventDefault();
                this.goToPrevious();
                break;
            case 'ArrowRight':
                e.preventDefault();
                this.goToNext();
                break;
            case ' ':
                e.preventDefault();
                this.toggleAutoPlay();
                break;
            case 'Home':
                e.preventDefault();
                this.goToFirst();
                break;
            case 'End':
                e.preventDefault();
                this.goToLast();
                break;
            case 'PageUp':
                e.preventDefault();
                this.prevPage();
                break;
            case 'PageDown':
                e.preventDefault();
                this.nextPage();
                break;
            case 'r':
            case 'R':
                e.preventDefault();
                this.resetZoom();
                break;
            case 'm':
            case 'M':
                e.preventDefault();
                this.showAddMarkerHelp();
                break;
        }
    }

    async applyFilters() {
        // Get filter values
        this.filters.cf = document.getElementById('cf-filter').value;
        this.filters.name = document.getElementById('name-filter').value;
        this.filters.instance = document.getElementById('instance-filter').value;
        this.filters.timeRange = document.getElementById('time-filter').value;

        // Reset to first page and reload
        this.currentPage = 1;
        await this.loadScans(1);
        
        if (this.scans.length > 0) {
            await this.displayScan(0);
        }

        this.showStatus('Filters applied', 'success');
    }

    async clearFilters() {
        // Clear filter inputs
        document.getElementById('cf-filter').value = '';
        document.getElementById('name-filter').value = '';
        document.getElementById('instance-filter').value = '';
        document.getElementById('time-filter').value = '24h';

        // Clear filter state
        this.filters = {
            cf: '',
            name: '',
            instance: '',
            timeRange: '24h'
        };

        // Reload data
        await this.loadScans(1);
        
        if (this.scans.length > 0) {
            await this.displayScan(0);
        }

        this.showStatus('Filters cleared', 'success');
    }

    async applyAnalysis() {
        const presetId = document.getElementById('analysis-preset').value;
        
        if (!presetId || !this.currentScan) {
            this.showStatus('Please select an analysis preset and ensure a scan is loaded', 'warning');
            return;
        }

        try {
            const response = await fetch(`/api/analysis/apply/${this.currentScan.scan_id}?preset_id=${presetId}`);
            const result = await response.json();
            
            if (result.error) {
                throw new Error(result.error);
            }

            this.displayAnalysisResults(result);
            this.showStatus(`Applied ${result.preset_name} analysis`, 'success');
            
        } catch (error) {
            console.error('Error applying analysis:', error);
            this.showStatus('Error applying analysis: ' + error.message, 'error');
        }
    }

    displayAnalysisResults(analysisResult) {
        const resultsDiv = document.getElementById('analysis-results');
        const analysis = analysisResult.analysis;
        
        let html = `<h4>${analysisResult.preset_name}</h4>`;
        
        if (analysis.type === 'peak_detection') {
            const peaks = analysis.results;
            html += `<p>Found ${peaks.length} peaks:</p>`;
            peaks.slice(0, 10).forEach((peak, index) => {
                html += `
                    <div class="analysis-item">
                        <strong>Peak ${index + 1}:</strong> 
                        ${peak.frequency_mhz.toFixed(2)} MHz, 
                        ${peak.power_dbm.toFixed(2)} dBm
                        <br><small>Prominence: ${peak.prominence.toFixed(1)} dB</small>
                    </div>
                `;
            });
        } else if (analysis.type === 'signal_analysis') {
            const stats = analysis.results;
            html += `
                <div class="analysis-item">
                    <strong>Overall Statistics:</strong><br>
                    Max Power: ${stats.overall.max_power.toFixed(2)} dBm<br>
                    Min Power: ${stats.overall.min_power.toFixed(2)} dBm<br>
                    Mean Power: ${stats.overall.mean_power.toFixed(2)} dBm<br>
                    Std Dev: ${stats.overall.std_power.toFixed(2)} dB
                </div>
            `;
            
            if (stats.bands) {
                Object.entries(stats.bands).forEach(([bandName, bandStats]) => {
                    html += `
                        <div class="analysis-item">
                            <strong>${bandName}:</strong><br>
                            Max: ${bandStats.max_power.toFixed(2)} dBm<br>
                            Mean: ${bandStats.mean_power.toFixed(2)} dBm
                        </div>
                    `;
                });
            }
        } else if (analysis.type === 'interference') {
            const interference = analysis.results;
            html += `<p>Found ${interference.length} interference sources:</p>`;
            interference.slice(0, 5).forEach((source, index) => {
                html += `
                    <div class="analysis-item">
                        <strong>Source ${index + 1}:</strong><br>
                        ${source.center_frequency_mhz.toFixed(2)} MHz<br>
                        BW: ${source.bandwidth_mhz.toFixed(2)} MHz<br>
                        Max: ${source.max_power_dbm.toFixed(2)} dBm
                    </div>
                `;
            });
        }
        
        resultsDiv.innerHTML = html;
    }

    openMarkerDialog(frequency, power) {
        this.pendingMarker = { frequency, power };
        
        document.getElementById('marker-frequency').value = frequency.toFixed(3);
        document.getElementById('marker-power').value = power.toFixed(2);
        document.getElementById('marker-name').value = `Marker_${this.markerCounter}`;
        document.getElementById('marker-type').value = 'manual';
        document.getElementById('marker-notes').value = '';
        
        document.getElementById('marker-dialog').style.display = 'flex';
    }

    async saveMarker() {
        if (!this.pendingMarker || !this.currentScan) {
            this.closeMarkerDialog();
            return;
        }

        const markerData = {
            scan_id: this.currentScan.scan_id,
            marker_name: document.getElementById('marker-name').value,
            frequency_mhz: parseFloat(document.getElementById('marker-frequency').value),
            power_dbm: parseFloat(document.getElementById('marker-power').value),
            marker_type: document.getElementById('marker-type').value,
            notes: document.getElementById('marker-notes').value
        };

        try {
            const response = await fetch('/api/markers', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(markerData)
            });

            const result = await response.json();
            
            if (result.error) {
                throw new Error(result.error);
            }

            // Add marker to current scan and update display
            if (!this.currentScan.markers) {
                this.currentScan.markers = [];
            }
            this.currentScan.markers.push(result);
            this.markers = this.currentScan.markers;
            
            this.updateMarkersDisplay();
            this.markerCounter++;
            
            // Redraw plot to show new marker
            await this.displayScan(this.currentScanIndex);
            
            this.showStatus('Marker added successfully', 'success');
            this.closeMarkerDialog();
            
        } catch (error) {
            console.error('Error saving marker:', error);
            this.showStatus('Error saving marker: ' + error.message, 'error');
        }
    }

    closeMarkerDialog() {
        document.getElementById('marker-dialog').style.display = 'none';
        this.pendingMarker = null;
    }

    showAddMarkerHelp() {
        this.showStatus('Click on the spectrum plot to add a marker at that point', 'info');
    }

    async deleteMarker(markerId) {
        try {
            const response = await fetch(`/api/markers/${markerId}`, {
                method: 'DELETE'
            });

            const result = await response.json();
            
            if (result.error) {
                throw new Error(result.error);
            }

            // Remove marker from current scan
            if (this.currentScan.markers) {
                this.currentScan.markers = this.currentScan.markers.filter(m => m.id !== markerId);
                this.markers = this.currentScan.markers;
            }
            
            this.updateMarkersDisplay();
            
            // Redraw plot to remove marker
            await this.displayScan(this.currentScanIndex);
            
            this.showStatus('Marker deleted', 'success');
            
        } catch (error) {
            console.error('Error deleting marker:', error);
            this.showStatus('Error deleting marker: ' + error.message, 'error');
        }
    }

    updateMarkersDisplay() {
        const markersList = document.getElementById('markers-list');
        
        if (!this.markers || this.markers.length === 0) {
            markersList.innerHTML = '<div class="no-markers">No markers added</div>';
            return;
        }

        const markersHTML = this.markers.map(marker => {
            const timestamp = new Date(marker.created_at).toLocaleString();
            return `
                <div class="marker-item">
                    <div class="marker-info">
                        <div class="marker-name">${marker.marker_name}</div>
                        <div class="marker-freq">${marker.frequency_mhz.toFixed(3)} MHz</div>
                        <div class="marker-power">${marker.power_dbm.toFixed(2)} dBm</div>
                        <div class="marker-type">${marker.marker_type}</div>
                        ${marker.notes ? `<div class="marker-notes">${marker.notes}</div>` : ''}
                        <div class="marker-time">${timestamp}</div>
                    </div>
                    <button class="marker-remove" onclick="analyzer.deleteMarker(${marker.id})">
                        <i class="fas fa-times"></i>
                    </button>
                </div>
            `;
        }).join('');

        markersList.innerHTML = markersHTML;
    }

    clearMarkers() {
        if (!this.currentScan || !this.currentScan.markers || this.currentScan.markers.length === 0) {
            this.showStatus('No markers to clear', 'info');
            return;
        }

        if (confirm('Are you sure you want to clear all markers for this scan?')) {
            // Delete all markers for current scan
            const deletePromises = this.currentScan.markers.map(marker => 
                fetch(`/api/markers/${marker.id}`, { method: 'DELETE' })
            );

            Promise.all(deletePromises).then(() => {
                this.currentScan.markers = [];
                this.markers = [];
                this.updateMarkersDisplay();
                this.displayScan(this.currentScanIndex);
                this.showStatus('All markers cleared', 'success');
            }).catch(error => {
                console.error('Error clearing markers:', error);
                this.showStatus('Error clearing markers', 'error');
            });
        }
    }

    resetZoom() {
        const plotDiv = document.getElementById('rf-plot');
        Plotly.relayout(plotDiv, {
            'xaxis.autorange': true,
            'yaxis.autorange': true
        });
        this.showStatus('Zoom reset', 'success');
    }

    // Navigation methods
    goToFirst() {
        if (this.scans.length > 0) {
            this.displayScan(0);
        }
    }

    async goToPrevious() {
        if (this.currentScanIndex > 0) {
            await this.displayScan(this.currentScanIndex - 1);
        } else if (this.hasPrev) {
            await this.prevPage();
            if (this.scans.length > 0) {
                await this.displayScan(this.scans.length - 1);
            }
        } else if (this.socket && this.currentScan) {
            // Use WebSocket for fast navigation
            this.socket.emit('keyboard_navigation', {
                current_time: this.currentScan.scan_time,
                direction: 'prev'
            });
        }
    }

    async goToNext() {
        if (this.currentScanIndex < this.scans.length - 1) {
            await this.displayScan(this.currentScanIndex + 1);
        } else if (this.hasNext) {
            await this.nextPage();
            if (this.scans.length > 0) {
                await this.displayScan(0);
            }
        } else if (this.socket && this.currentScan) {
            // Use WebSocket for fast navigation
            this.socket.emit('keyboard_navigation', {
                current_time: this.currentScan.scan_time,
                direction: 'next'
            });
        }
    }

    goToLast() {
        if (this.scans.length > 0) {
            this.displayScan(this.scans.length - 1);
        }
    }

    async nextPage() {
        if (this.hasNext) {
            await this.loadScans(this.currentPage + 1);
            this.currentScanIndex = 0;
            if (this.scans.length > 0) {
                await this.displayScan(0);
            }
        }
    }

    async prevPage() {
        if (this.hasPrev) {
            await this.loadScans(this.currentPage - 1);
            this.currentScanIndex = 0;
            if (this.scans.length > 0) {
                await this.displayScan(0);
            }
        }
    }

    toggleAutoPlay() {
        if (this.isPlaying) {
            this.stopAutoPlay();
        } else {
            this.startAutoPlay();
        }
    }

    startAutoPlay() {
        const playButton = document.getElementById('play-btn');
        const speed = parseInt(document.getElementById('playback-speed').value);
        
        this.isPlaying = true;
        playButton.innerHTML = '<i class="fas fa-pause"></i>';
        playButton.title = 'Pause Auto Play';
        
        this.playInterval = setInterval(() => {
            this.goToNext();
        }, speed);
        
        this.showStatus('Auto-play started', 'info');
    }

    stopAutoPlay() {
        const playButton = document.getElementById('play-btn');
        
        this.isPlaying = false;
        playButton.innerHTML = '<i class="fas fa-play"></i>';
        playButton.title = 'Start Auto Play';
        
        if (this.playInterval) {
            clearInterval(this.playInterval);
            this.playInterval = null;
        }
        
        this.showStatus('Auto-play stopped', 'info');
    }

    updateInfo() {
        document.getElementById('current-scan').textContent = this.currentScanIndex + 1;
        document.getElementById('total-scans').textContent = this.totalScans;
        document.getElementById('current-page').textContent = this.currentPage;
        document.getElementById('total-pages').textContent = this.totalPages;
        document.getElementById('page-display').textContent = this.currentPage;
    }

    updateScanInfo() {
        if (!this.currentScan) return;
        
        const config = this.currentScan.config_info;
        const timestamp = new Date(this.currentScan.scan_time).toLocaleString();
        
        document.getElementById('current-timestamp').textContent = timestamp;
        document.getElementById('current-cf').textContent = config.cf || '-';
        document.getElementById('current-span').textContent = config.span || '-';
        document.getElementById('current-instance').textContent = this.currentScan.instance_name || '-';
        document.getElementById('current-config').textContent = config.name || '-';
    }

    updatePaginationButtons() {
        document.getElementById('prev-page-btn').disabled = !this.hasPrev;
        document.getElementById('next-page-btn').disabled = !this.hasNext;
    }

    showLoading() {
        document.getElementById('loading').style.display = 'flex';
    }

    hideLoading() {
        document.getElementById('loading').style.display = 'none';
    }

    showStatus(message, type = 'info') {
        const statusText = document.getElementById('status-text');
        statusText.textContent = message;
        statusText.className = `status-${type}`;
        
        // Auto-clear status after 5 seconds
        setTimeout(() => {
            if (statusText.textContent === message) {
                statusText.textContent = 'Ready - Use arrow keys to navigate, space to play/pause';
                statusText.className = '';
            }
        }, 5000);
    }
}

// Global functions for HTML onclick handlers
function closeMarkerDialog() {
    analyzer.closeMarkerDialog();
}

function saveMarker() {
    analyzer.saveMarker();
}

// Initialize the application
let analyzer;
document.addEventListener('DOMContentLoaded', () => {
    analyzer = new RFSpectrumAnalyzer();
});