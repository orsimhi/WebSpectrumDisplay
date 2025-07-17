// RF Spectrum Analyzer - Main Application
class RFSpectrumAnalyzer {
    constructor() {
        this.socket = null;
        this.currentPage = 1;
        this.totalPages = 1;
        this.totalRecords = 0;
        this.autoPlay = false;
        this.markers = [];
        this.currentData = null;
        
        this.init();
    }
    
    init() {
        this.initSocketIO();
        this.initEventListeners();
        this.initKeyboardShortcuts();
        this.loadInitialData();
    }
    
    initSocketIO() {
        this.socket = io();
        
        this.socket.on('connect', () => {
            console.log('Connected to server');
            this.updateConnectionStatus(true);
        });
        
        this.socket.on('disconnect', () => {
            console.log('Disconnected from server');
            this.updateConnectionStatus(false);
        });
        
        this.socket.on('status', (data) => {
            console.log('Status:', data.msg);
        });
        
        this.socket.on('autoplay_status', (data) => {
            this.autoPlay = data.enabled;
            this.updateAutoPlayButton();
        });
        
        this.socket.on('autoplay_next', (data) => {
            if (this.autoPlay && this.currentPage < this.totalPages) {
                this.nextRecord();
            }
        });
    }
    
    initEventListeners() {
        // Navigation controls
        document.getElementById('firstBtn').addEventListener('click', () => this.firstRecord());
        document.getElementById('prevBtn').addEventListener('click', () => this.prevRecord());
        document.getElementById('nextBtn').addEventListener('click', () => this.nextRecord());
        document.getElementById('lastBtn').addEventListener('click', () => this.lastRecord());
        document.getElementById('autoplayBtn').addEventListener('click', () => this.toggleAutoPlay());
        
        // Analysis controls
        document.getElementById('peakAnalysisBtn').addEventListener('click', () => this.performPeakAnalysis());
        document.getElementById('occupancyBtn').addEventListener('click', () => this.performOccupancyAnalysis());
        document.getElementById('clearMarkersBtn').addEventListener('click', () => this.clearMarkers());
        document.getElementById('resetZoomBtn').addEventListener('click', () => this.resetZoom());
        
        // Hold-to-navigate functionality
        this.setupHoldToNavigate('prevBtn', () => this.prevRecord());
        this.setupHoldToNavigate('nextBtn', () => this.nextRecord());
    }
    
    setupHoldToNavigate(buttonId, action) {
        const button = document.getElementById(buttonId);
        let holdTimer = null;
        let holdInterval = null;
        
        const startHold = () => {
            holdTimer = setTimeout(() => {
                holdInterval = setInterval(action, 200);
            }, 500);
        };
        
        const stopHold = () => {
            if (holdTimer) {
                clearTimeout(holdTimer);
                holdTimer = null;
            }
            if (holdInterval) {
                clearInterval(holdInterval);
                holdInterval = null;
            }
        };
        
        button.addEventListener('mousedown', startHold);
        button.addEventListener('mouseup', stopHold);
        button.addEventListener('mouseleave', stopHold);
        button.addEventListener('touchstart', startHold);
        button.addEventListener('touchend', stopHold);
    }
    
    initKeyboardShortcuts() {
        document.addEventListener('keydown', (e) => {
            // Ignore if typing in input fields
            if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA') {
                return;
            }
            
            switch(e.key) {
                case 'ArrowLeft':
                    e.preventDefault();
                    this.prevRecord();
                    break;
                case 'ArrowRight':
                    e.preventDefault();
                    this.nextRecord();
                    break;
                case 'Home':
                    e.preventDefault();
                    this.firstRecord();
                    break;
                case 'End':
                    e.preventDefault();
                    this.lastRecord();
                    break;
                case ' ':
                    e.preventDefault();
                    this.toggleAutoPlay();
                    break;
                case 'p':
                case 'P':
                    e.preventDefault();
                    this.performPeakAnalysis();
                    break;
                case 'o':
                case 'O':
                    e.preventDefault();
                    this.performOccupancyAnalysis();
                    break;
                case 'c':
                case 'C':
                    e.preventDefault();
                    this.clearMarkers();
                    break;
                case 'r':
                case 'R':
                    e.preventDefault();
                    this.resetZoom();
                    break;
                case '?':
                    e.preventDefault();
                    this.showKeyboardShortcuts();
                    break;
            }
        });
    }
    
    showKeyboardShortcuts() {
        const modal = new bootstrap.Modal(document.getElementById('shortcutsModal'));
        modal.show();
    }
    
    updateConnectionStatus(connected) {
        const status = document.getElementById('connectionStatus');
        if (connected) {
            status.innerHTML = '<i class="fas fa-circle text-success me-1"></i><span>Connected</span>';
            status.className = 'connection-status connected';
        } else {
            status.innerHTML = '<i class="fas fa-circle text-danger me-1"></i><span>Disconnected</span>';
            status.className = 'connection-status disconnected';
        }
    }
    
    showLoading() {
        document.getElementById('loadingSpinner').classList.add('show');
    }
    
    hideLoading() {
        document.getElementById('loadingSpinner').classList.remove('show');
    }
    
    loadInitialData() {
        this.loadSpectrumData(1);
    }
    
    async loadSpectrumData(page) {
        this.showLoading();
        
        try {
            const response = await fetch(`/api/spectrum_data?page=${page}&per_page=1`);
            const data = await response.json();
            
            if (data.error) {
                this.showError('Error loading spectrum data: ' + data.error);
                return;
            }
            
            this.currentData = data;
            this.currentPage = data.pagination.current_page;
            this.totalPages = data.pagination.total_pages;
            this.totalRecords = data.pagination.total_records;
            
            this.updatePagination();
            this.updateMetadata(data.metadata);
            this.plotSpectrum(data.frequencies, data.powers);
            
        } catch (error) {
            this.showError('Failed to load spectrum data: ' + error.message);
        } finally {
            this.hideLoading();
        }
    }
    
    plotSpectrum(frequencies, powers) {
        const trace = {
            x: frequencies.map(f => f / 1e6), // Convert to MHz
            y: powers,
            type: 'scatter',
            mode: 'lines',
            name: 'RF Spectrum',
            line: {
                color: '#00ff88',
                width: 1.5
            },
            hovertemplate: 'Frequency: %{x:.2f} MHz<br>Power: %{y:.2f} dBm<extra></extra>'
        };
        
        const layout = {
            title: {
                text: 'RF Spectrum Analysis',
                font: { color: 'white', size: 16 }
            },
            xaxis: {
                title: 'Frequency (MHz)',
                color: 'white',
                gridcolor: 'rgba(255,255,255,0.1)',
                tickformat: '.0f'
            },
            yaxis: {
                title: 'Power (dBm)',
                color: 'white',
                gridcolor: 'rgba(255,255,255,0.1)',
                tickformat: '.0f'
            },
            plot_bgcolor: '#1a1a1a',
            paper_bgcolor: '#1a1a1a',
            font: { color: 'white' },
            showlegend: false,
            margin: { l: 60, r: 30, t: 50, b: 60 },
            hovermode: 'x unified'
        };
        
        const config = {
            responsive: true,
            displayModeBar: true,
            modeBarButtons: [
                ['zoom2d', 'pan2d', 'select2d', 'lasso2d'],
                ['zoomIn2d', 'zoomOut2d', 'autoScale2d', 'resetScale2d'],
                ['toImage']
            ],
            displaylogo: false
        };
        
        Plotly.newPlot('spectrumPlot', [trace], layout, config);
        
        // Add click handler for markers
        document.getElementById('spectrumPlot').on('plotly_click', (data) => {
            if (data.points.length > 0) {
                const point = data.points[0];
                const frequency = point.x * 1e6; // Convert back to Hz
                const power = point.y;
                this.addMarker(frequency, power);
            }
        });
    }
    
    updatePagination() {
        document.getElementById('currentPage').textContent = this.currentPage;
        document.getElementById('totalPages').textContent = this.totalPages;
        document.getElementById('totalRecords').textContent = this.totalRecords;
        
        // Update button states
        document.getElementById('firstBtn').disabled = this.currentPage === 1;
        document.getElementById('prevBtn').disabled = this.currentPage === 1;
        document.getElementById('nextBtn').disabled = this.currentPage === this.totalPages;
        document.getElementById('lastBtn').disabled = this.currentPage === this.totalPages;
    }
    
    updateMetadata(metadata) {
        document.getElementById('timestamp').textContent = new Date(metadata.timestamp).toLocaleString();
        document.getElementById('deviceId').textContent = metadata.device_id;
        document.getElementById('measurementType').textContent = metadata.measurement_type;
        document.getElementById('bandwidth').textContent = (metadata.bandwidth / 1000).toFixed(1) + ' kHz';
        document.getElementById('gain').textContent = metadata.gain + ' dB';
    }
    
    // Navigation methods
    firstRecord() {
        if (this.currentPage !== 1) {
            this.loadSpectrumData(1);
        }
    }
    
    prevRecord() {
        if (this.currentPage > 1) {
            this.loadSpectrumData(this.currentPage - 1);
        }
    }
    
    nextRecord() {
        if (this.currentPage < this.totalPages) {
            this.loadSpectrumData(this.currentPage + 1);
        }
    }
    
    lastRecord() {
        if (this.currentPage !== this.totalPages) {
            this.loadSpectrumData(this.totalPages);
        }
    }
    
    toggleAutoPlay() {
        this.socket.emit('toggle_autoplay');
    }
    
    updateAutoPlayButton() {
        const button = document.getElementById('autoplayBtn');
        if (this.autoPlay) {
            button.classList.add('autoplay-active');
            button.innerHTML = '<i class="fas fa-pause"></i>';
            button.title = 'Stop Auto-play';
        } else {
            button.classList.remove('autoplay-active');
            button.innerHTML = '<i class="fas fa-play"></i>';
            button.title = 'Start Auto-play';
        }
    }
    
    // Analysis methods
    async performPeakAnalysis() {
        if (!this.currentData) return;
        
        try {
            const threshold = -70; // dBm
            const response = await fetch(`/api/analysis/peak_detection?page=${this.currentPage}&threshold=${threshold}`);
            const data = await response.json();
            
            if (data.error) {
                this.showError('Peak analysis failed: ' + data.error);
                return;
            }
            
            this.displayPeakAnalysis(data);
            
        } catch (error) {
            this.showError('Peak analysis failed: ' + error.message);
        }
    }
    
    displayPeakAnalysis(data) {
        const container = document.getElementById('analysisResults');
        
        let html = `
            <div class="analysis-item peak-item">
                <h6><i class="fas fa-mountain me-2"></i>Peak Detection Results</h6>
                <div class="stats">
                    <div class="stat">
                        <span class="stat-label">Total Peaks:</span>
                        <span class="stat-value">${data.analysis.total_peaks}</span>
                    </div>
                    <div class="stat">
                        <span class="stat-label">Avg Power:</span>
                        <span class="stat-value">${data.analysis.average_power.toFixed(1)} dBm</span>
                    </div>
                    <div class="stat">
                        <span class="stat-label">Noise Floor:</span>
                        <span class="stat-value">${data.analysis.noise_floor.toFixed(1)} dBm</span>
                    </div>
                    <div class="stat">
                        <span class="stat-label">Dynamic Range:</span>
                        <span class="stat-value">${data.analysis.dynamic_range.toFixed(1)} dB</span>
                    </div>
                </div>
        `;
        
        if (data.peaks.length > 0) {
            html += '<div class="mt-2"><strong>Top Peaks:</strong></div>';
            data.peaks.slice(0, 5).forEach((peak, i) => {
                html += `
                    <div class="peak-item mb-1 p-2" style="font-size: 0.8rem;">
                        <div class="d-flex justify-content-between">
                            <span class="frequency">${(peak.frequency / 1e6).toFixed(2)} MHz</span>
                            <span class="power">${peak.power.toFixed(1)} dBm</span>
                        </div>
                    </div>
                `;
            });
        }
        
        html += '</div>';
        container.innerHTML = html;
    }
    
    async performOccupancyAnalysis() {
        if (!this.currentData) return;
        
        try {
            const threshold = -80; // dBm
            const response = await fetch(`/api/analysis/occupancy?page=${this.currentPage}&threshold=${threshold}`);
            const data = await response.json();
            
            if (data.error) {
                this.showError('Occupancy analysis failed: ' + data.error);
                return;
            }
            
            this.displayOccupancyAnalysis(data);
            
        } catch (error) {
            this.showError('Occupancy analysis failed: ' + error.message);
        }
    }
    
    displayOccupancyAnalysis(data) {
        const container = document.getElementById('analysisResults');
        
        let html = `
            <div class="analysis-item occupancy-item">
                <h6><i class="fas fa-chart-bar me-2"></i>Spectrum Occupancy</h6>
                <div class="stats">
                    <div class="stat">
                        <span class="stat-label">Occupancy:</span>
                        <span class="stat-value">${data.occupancy_percentage.toFixed(1)}%</span>
                    </div>
                    <div class="stat">
                        <span class="stat-label">Total BW:</span>
                        <span class="stat-value">${(data.total_bandwidth / 1e6).toFixed(1)} MHz</span>
                    </div>
                    <div class="stat">
                        <span class="stat-label">Occupied BW:</span>
                        <span class="stat-value">${(data.occupied_bandwidth / 1e6).toFixed(1)} MHz</span>
                    </div>
                    <div class="stat">
                        <span class="stat-label">Active Bands:</span>
                        <span class="stat-value">${data.occupied_bands.length}</span>
                    </div>
                </div>
        `;
        
        if (data.occupied_bands.length > 0) {
            html += '<div class="mt-2"><strong>Occupied Bands:</strong></div>';
            data.occupied_bands.forEach(band => {
                html += `
                    <div class="band-item">
                        <div><strong>${(band.center_freq / 1e6).toFixed(2)} MHz</strong></div>
                        <div style="font-size: 0.75rem;">
                            ${(band.start_freq / 1e6).toFixed(2)} - ${(band.end_freq / 1e6).toFixed(2)} MHz
                            (${(band.bandwidth / 1e6).toFixed(2)} MHz)
                        </div>
                    </div>
                `;
            });
        }
        
        html += '</div>';
        container.innerHTML = html;
    }
    
    // Marker methods
    addMarker(frequency, power) {
        const marker = {
            id: Date.now(),
            frequency: frequency,
            power: power,
            timestamp: this.currentData?.metadata?.timestamp || new Date().toISOString()
        };
        
        this.markers.push(marker);
        this.updateMarkersDisplay();
        this.addMarkerToPlot(marker);
    }
    
    addMarkerToPlot(marker) {
        const markerTrace = {
            x: [marker.frequency / 1e6],
            y: [marker.power],
            mode: 'markers',
            marker: {
                color: '#ff6b6b',
                size: 10,
                symbol: 'diamond',
                line: { color: 'white', width: 2 }
            },
            name: `Marker ${marker.id}`,
            hovertemplate: `Marker<br>Frequency: %{x:.2f} MHz<br>Power: %{y:.2f} dBm<extra></extra>`
        };
        
        Plotly.addTraces('spectrumPlot', markerTrace);
    }
    
    removeMarker(markerId) {
        this.markers = this.markers.filter(m => m.id !== markerId);
        this.updateMarkersDisplay();
        this.refreshPlot();
    }
    
    clearMarkers() {
        this.markers = [];
        this.updateMarkersDisplay();
        this.refreshPlot();
    }
    
    updateMarkersDisplay() {
        const container = document.getElementById('markersList');
        
        if (this.markers.length === 0) {
            container.innerHTML = `
                <div class="text-muted text-center">
                    <i class="fas fa-mouse-pointer fa-2x mb-2"></i>
                    <p>Click on the spectrum to add markers</p>
                </div>
            `;
            return;
        }
        
        let html = '';
        this.markers.forEach(marker => {
            html += `
                <div class="marker-item">
                    <div class="marker-info">
                        <div class="marker-freq">${(marker.frequency / 1e6).toFixed(2)} MHz</div>
                        <div class="marker-power">${marker.power.toFixed(1)} dBm</div>
                    </div>
                    <button class="marker-remove" onclick="app.removeMarker(${marker.id})">
                        <i class="fas fa-times"></i>
                    </button>
                </div>
            `;
        });
        
        container.innerHTML = html;
    }
    
    refreshPlot() {
        if (this.currentData) {
            this.plotSpectrum(this.currentData.frequencies, this.currentData.powers);
            // Re-add markers
            this.markers.forEach(marker => this.addMarkerToPlot(marker));
        }
    }
    
    resetZoom() {
        Plotly.relayout('spectrumPlot', {
            'xaxis.autorange': true,
            'yaxis.autorange': true
        });
    }
    
    showError(message) {
        console.error(message);
        // You could implement toast notifications here
        alert(message);
    }
}

// Initialize the application when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.app = new RFSpectrumAnalyzer();
});