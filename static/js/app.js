class RFAmplitudeViewer {
    constructor() {
        this.data = [];
        this.currentIndex = 0;
        this.currentPage = 1;
        this.totalPages = 1;
        this.totalRecords = 0;
        this.perPage = 20;
        this.markers = [];
        this.isPlaying = false;
        this.playInterval = null;
        this.isMarkerMode = true;
        this.holdTimeout = null;
        this.holdInterval = null;
        this.autoReload = false;
        this.socket = null;
        
        this.init();
    }

    async init() {
        this.initializeWebSocket();
        await this.loadData();
        this.setupEventListeners();
        if (this.data.length > 0) {
            await this.displayRecord(0);
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

            this.socket.on('live_data_update', (data) => {
                if (this.autoReload && data && data.length > 0) {
                    this.handleLiveDataUpdate(data);
                }
            });

            this.socket.on('error', (error) => {
                console.error('WebSocket error:', error);
                this.showStatus(`WebSocket error: ${error.msg}`, 'error');
            });

        } catch (error) {
            console.warn('WebSocket not available:', error);
            this.showStatus('Real-time updates not available', 'warning');
        }
    }

    handleLiveDataUpdate(newData) {
        // Check if this is actually new data
        const latestTimestamp = newData[0].timestamp;
        const existingRecord = this.data.find(record => record.timestamp === latestTimestamp);
        
        if (!existingRecord) {
            // Add new data to the beginning of our dataset
            this.data.unshift(...newData);
            this.totalRecords++;
            this.updateInfo();
            this.showStatus('New RF data received', 'info');
            
            // If we're on the first page and first record, auto-update the display
            if (this.currentPage === 1 && this.currentIndex === 0) {
                this.displayRecord(0);
            }
        }
    }

    async loadData(page = 1, append = false) {
        try {
            const response = await fetch(`/api/rf_data?page=${page}&per_page=${this.perPage}`);
            const result = await response.json();
            
            if (result.error) {
                throw new Error(result.error);
            }

            if (append) {
                this.data.push(...result.records);
            } else {
                this.data = result.records;
            }
            
            this.currentPage = result.page;
            this.totalPages = Math.ceil(result.total / result.per_page);
            this.totalRecords = result.total;
            this.hasNext = result.has_next;
            this.hasPrev = result.has_prev;
            
            this.updateInfo();
            this.updatePaginationButtons();
            
        } catch (error) {
            console.error('Error loading RF data:', error);
            this.showStatus('Error loading data: ' + error.message, 'error');
        }
    }

    async loadMoreData() {
        if (this.hasNext) {
            await this.loadData(this.currentPage + 1, true);
            this.showStatus('Loaded more RF data', 'success');
        } else {
            this.showStatus('No more data to load', 'info');
        }
    }

    async nextPage() {
        if (this.hasNext) {
            await this.loadData(this.currentPage + 1);
            this.currentIndex = 0;
            if (this.data.length > 0) {
                await this.displayRecord(0);
            }
        }
    }

    async prevPage() {
        if (this.hasPrev) {
            await this.loadData(this.currentPage - 1);
            this.currentIndex = 0;
            if (this.data.length > 0) {
                await this.displayRecord(0);
            }
        }
    }

    setupEventListeners() {
        // Navigation buttons
        document.getElementById('first-btn').addEventListener('click', () => this.goToFirst());
        document.getElementById('prev-btn').addEventListener('click', () => this.goToPrevious());
        document.getElementById('next-btn').addEventListener('click', () => this.goToNext());
        document.getElementById('last-btn').addEventListener('click', () => this.goToLast());
        document.getElementById('play-btn').addEventListener('click', () => this.toggleAutoPlay());

        // Pagination buttons
        document.getElementById('prev-page-btn').addEventListener('click', () => this.prevPage());
        document.getElementById('next-page-btn').addEventListener('click', () => this.nextPage());
        document.getElementById('load-more-btn').addEventListener('click', () => this.loadMoreData());

        // Tool buttons
        document.getElementById('add-marker-btn').addEventListener('click', () => this.toggleMarkerMode());
        document.getElementById('clear-markers-btn').addEventListener('click', () => this.clearMarkers());
        document.getElementById('reset-zoom-btn').addEventListener('click', () => this.resetZoom());
        document.getElementById('auto-reload-btn').addEventListener('click', () => this.toggleAutoReload());

        // Hold to navigate
        this.setupHoldNavigation('prev-btn', () => this.goToPrevious());
        this.setupHoldNavigation('next-btn', () => this.goToNext());

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

    setupHoldNavigation(buttonId, action) {
        const button = document.getElementById(buttonId);
        
        button.addEventListener('mousedown', () => {
            this.holdTimeout = setTimeout(() => {
                this.holdInterval = setInterval(action, 100);
            }, 500);
        });

        button.addEventListener('mouseup', () => {
            clearTimeout(this.holdTimeout);
            clearInterval(this.holdInterval);
        });

        button.addEventListener('mouseleave', () => {
            clearTimeout(this.holdTimeout);
            clearInterval(this.holdInterval);
        });
    }

    handleKeyboard(e) {
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
            case 'Escape':
                e.preventDefault();
                this.resetZoom();
                break;
            case 'c':
                e.preventDefault();
                this.clearMarkers();
                break;
            case 'm':
                e.preventDefault();
                this.toggleMarkerMode();
                break;
            case 'r':
                e.preventDefault();
                this.toggleAutoReload();
                break;
            case 'PageDown':
                e.preventDefault();
                this.nextPage();
                break;
            case 'PageUp':
                e.preventDefault();
                this.prevPage();
                break;
        }
    }

    async displayRecord(index) {
        if (index < 0 || index >= this.data.length) return;
        
        this.currentIndex = index;
        this.updateInfo();
        this.updateNavigationButtons();
        
        try {
            const recordId = this.data[index].id;
            const response = await fetch(`/api/plot/${recordId}`);
            const plotData = await response.json();
            
            if (plotData.error) {
                throw new Error(plotData.error);
            }
            
            await this.renderPlot(plotData);
            this.showStatus(`Displaying record ${index + 1} of ${this.data.length} (Page ${this.currentPage})`, 'success');
        } catch (error) {
            console.error('Error displaying record:', error);
            this.showStatus('Error displaying record: ' + error.message, 'error');
        }
    }

    async renderPlot(plotData) {
        const plotDiv = document.getElementById('rf-plot');
        
        // Parse the plot data
        const figure = JSON.parse(plotData.plot);
        
        // Configure plot
        const config = {
            responsive: true,
            displayModeBar: true,
            modeBarButtonsToAdd: ['drawline', 'drawopenpath', 'drawclosedpath'],
            modeBarButtonsToRemove: ['pan2d', 'select2d', 'lasso2d'],
            displaylogo: false
        };

        // Plot the figure
        await Plotly.newPlot(plotDiv, figure.data, figure.layout, config);
        
        // Store current data for markers
        this.currentPlotData = {
            frequencies: plotData.frequencies,
            powers: plotData.powers,
            center_frequency: plotData.center_frequency,
            span: plotData.span
        };

        // Setup plot event listeners
        this.setupPlotEvents(plotDiv);
        
        // Redraw existing markers
        this.redrawMarkers();
    }

    setupPlotEvents(plotDiv) {
        // Click event for adding markers
        plotDiv.on('plotly_click', (data) => {
            if (this.isMarkerMode && data.points.length > 0) {
                const point = data.points[0];
                this.addMarker(point.x, point.y);
            }
        });

        // Hover event for cursor info
        plotDiv.on('plotly_hover', (data) => {
            if (data.points.length > 0) {
                const point = data.points[0];
                const freq = point.x.toFixed(2);
                const power = point.y.toFixed(2);
                document.getElementById('cursor-info').textContent = 
                    `Frequency: ${freq} MHz, Power: ${power} dBm`;
            }
        });

        plotDiv.on('plotly_unhover', () => {
            document.getElementById('cursor-info').textContent = 
                'Move cursor over graph for details';
        });
    }

    addMarker(frequency, power) {
        const markerId = Date.now();
        const marker = {
            id: markerId,
            frequency: frequency,
            power: power,
            recordIndex: this.currentIndex,
            recordId: this.data[this.currentIndex].id,
            timestamp: this.data[this.currentIndex].timestamp
        };
        
        this.markers.push(marker);
        this.updateMarkersDisplay();
        this.redrawMarkers();
        
        this.showStatus(`Marker added at ${frequency.toFixed(2)} MHz`, 'success');
    }

    removeMarker(markerId) {
        this.markers = this.markers.filter(m => m.id !== markerId);
        this.updateMarkersDisplay();
        this.redrawMarkers();
        this.showStatus('Marker removed', 'success');
    }

    clearMarkers() {
        this.markers = [];
        this.updateMarkersDisplay();
        this.redrawMarkers();
        this.showStatus('All markers cleared', 'success');
    }

    redrawMarkers() {
        const plotDiv = document.getElementById('rf-plot');
        if (!plotDiv.data) return;

        // Remove existing marker traces
        const traces = plotDiv.data.filter(trace => !trace.name.includes('Marker'));
        
        // Add marker traces for current record
        const currentRecordId = this.data[this.currentIndex]?.id;
        const currentMarkers = this.markers.filter(m => m.recordId === currentRecordId);
        
        currentMarkers.forEach(marker => {
            traces.push({
                x: [marker.frequency],
                y: [marker.power],
                mode: 'markers',
                marker: {
                    size: 12,
                    color: '#ff6b6b',
                    symbol: 'diamond',
                    line: {
                        width: 2,
                        color: '#ffffff'
                    }
                },
                name: `Marker ${marker.id}`,
                showlegend: false,
                hovertemplate: `<b>Marker</b><br>Frequency: %{x:.2f} MHz<br>Power: %{y:.2f} dBm<extra></extra>`
            });
        });

        Plotly.redraw(plotDiv);
    }

    updateMarkersDisplay() {
        const markersList = document.getElementById('markers-list');
        
        if (this.markers.length === 0) {
            markersList.innerHTML = '<div class="no-markers">No markers added</div>';
            return;
        }

        const markersHTML = this.markers.map(marker => {
            const recordNum = marker.recordIndex + 1;
            const timestamp = new Date(marker.timestamp).toLocaleString();
            return `
                <div class="marker-item">
                    <div class="marker-info">
                        <span class="marker-freq">${marker.frequency.toFixed(2)} MHz</span>
                        <span class="marker-power">${marker.power.toFixed(2)} dBm</span>
                        <span class="marker-record">Record ${recordNum}</span>
                        <span class="marker-time">${timestamp}</span>
                    </div>
                    <button class="marker-remove" onclick="viewer.removeMarker(${marker.id})">
                        <i class="fas fa-times"></i>
                    </button>
                </div>
            `;
        }).join('');

        markersList.innerHTML = markersHTML;
    }

    toggleMarkerMode() {
        this.isMarkerMode = !this.isMarkerMode;
        const button = document.getElementById('add-marker-btn');
        
        if (this.isMarkerMode) {
            button.classList.add('active');
            button.innerHTML = '<i class="fas fa-map-pin"></i> Add Marker';
            this.showStatus('Click on graph to add markers', 'info');
        } else {
            button.classList.remove('active');
            button.innerHTML = '<i class="fas fa-map-pin"></i> Marker Mode Off';
            this.showStatus('Marker mode disabled', 'info');
        }
    }

    toggleAutoReload() {
        this.autoReload = !this.autoReload;
        const button = document.getElementById('auto-reload-btn');
        
        if (this.autoReload) {
            button.classList.add('auto-reload');
            button.innerHTML = '<i class="fas fa-sync-alt"></i> Auto Reload On';
            this.showStatus('Auto-reload enabled - new data will load automatically', 'info');
            
            // Request live updates
            if (this.socket) {
                this.socket.emit('request_live_update');
            }
        } else {
            button.classList.remove('auto-reload');
            button.innerHTML = '<i class="fas fa-sync-alt"></i> Auto Reload';
            this.showStatus('Auto-reload disabled', 'info');
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
        if (this.data.length > 0) {
            this.displayRecord(0);
        }
    }

    goToPrevious() {
        if (this.currentIndex > 0) {
            this.displayRecord(this.currentIndex - 1);
        } else if (this.hasPrev) {
            // Load previous page and go to last record
            this.prevPage().then(() => {
                if (this.data.length > 0) {
                    this.displayRecord(this.data.length - 1);
                }
            });
        }
    }

    goToNext() {
        if (this.currentIndex < this.data.length - 1) {
            this.displayRecord(this.currentIndex + 1);
        } else if (this.hasNext) {
            // Load next page and go to first record
            this.nextPage().then(() => {
                if (this.data.length > 0) {
                    this.displayRecord(0);
                }
            });
        }
    }

    goToLast() {
        if (this.data.length > 0) {
            this.displayRecord(this.data.length - 1);
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
        this.isPlaying = true;
        const button = document.getElementById('play-btn');
        button.classList.add('playing');
        button.innerHTML = '<i class="fas fa-pause"></i>';
        button.title = 'Pause Auto Play';
        
        const speed = parseInt(document.getElementById('playback-speed').value);
        this.playInterval = setInterval(() => {
            if (this.currentIndex < this.data.length - 1) {
                this.goToNext();
            } else if (this.hasNext) {
                this.goToNext(); // Will automatically load next page
            } else {
                this.stopAutoPlay();
            }
        }, speed);
        
        this.showStatus('Auto play started', 'info');
    }

    stopAutoPlay() {
        this.isPlaying = false;
        const button = document.getElementById('play-btn');
        button.classList.remove('playing');
        button.innerHTML = '<i class="fas fa-play"></i>';
        button.title = 'Auto Play';
        
        if (this.playInterval) {
            clearInterval(this.playInterval);
            this.playInterval = null;
        }
        
        this.showStatus('Auto play stopped', 'info');
    }

    updateNavigationButtons() {
        const isFirstRecord = this.currentIndex === 0 && !this.hasPrev;
        const isLastRecord = this.currentIndex === this.data.length - 1 && !this.hasNext;
        
        document.getElementById('first-btn').disabled = isFirstRecord;
        document.getElementById('prev-btn').disabled = isFirstRecord;
        document.getElementById('next-btn').disabled = isLastRecord;
        document.getElementById('last-btn').disabled = isLastRecord;
    }

    updatePaginationButtons() {
        document.getElementById('prev-page-btn').disabled = !this.hasPrev;
        document.getElementById('next-page-btn').disabled = !this.hasNext;
        document.getElementById('load-more-btn').disabled = !this.hasNext;
        document.getElementById('page-display').textContent = this.currentPage;
    }

    updateInfo() {
        document.getElementById('current-page').textContent = this.currentPage;
        document.getElementById('total-pages').textContent = this.totalPages;
        document.getElementById('total-records').textContent = this.totalRecords;
        
        if (this.data.length === 0) return;
        
        document.getElementById('current-record').textContent = 
            (this.currentPage - 1) * this.perPage + this.currentIndex + 1;
        
        if (this.data[this.currentIndex]) {
            const record = this.data[this.currentIndex];
            const timestamp = new Date(record.timestamp).toLocaleString();
            document.getElementById('current-timestamp').textContent = timestamp;
            document.getElementById('current-cf').textContent = record.center_frequency.toFixed(1);
            document.getElementById('current-span').textContent = record.span.toFixed(1);
            document.getElementById('current-device').textContent = record.device_id || 'Unknown';
        }
    }

    showStatus(message, type = 'info') {
        const statusText = document.getElementById('status-text');
        statusText.textContent = message;
        
        // Reset classes
        statusText.className = '';
        
        // Add type class
        statusText.classList.add(`status-${type}`);
        
        // Clear after 3 seconds
        setTimeout(() => {
            statusText.textContent = 'Ready';
            statusText.className = '';
        }, 3000);
    }

    hideLoading() {
        document.getElementById('loading').classList.add('hidden');
    }
}

// Initialize the application when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.viewer = new RFAmplitudeViewer();
});

// Add some additional CSS classes for status types
const style = document.createElement('style');
style.textContent = `
    .status-success { color: #4ade80 !important; }
    .status-error { color: #ef4444 !important; }
    .status-info { color: #3b82f6 !important; }
    .status-warning { color: #fbbf24 !important; }
    
    .marker-time {
        font-size: 0.8rem;
        opacity: 0.8;
        color: #94a3b8;
    }
`;
document.head.appendChild(style);