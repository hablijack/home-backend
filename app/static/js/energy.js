var EnergyDashboard = (function () {

    var fetchEnergyData = function () {
        return fetch('/api/energy').then(function (response) {
            if (response.ok) {
                return response.json();
            } else {
                return Promise.reject(response);
            }
        });
    };

    var fetchZoeData = function () {
        return fetch('/api/zoe/battery/current.json').then(function (response) {
            if (response.ok) {
                return response.json();
            } else {
                return Promise.reject(response);
            }
        });
    };

    var fetchHouseTempData = function () {
        return fetch('/api/house/temp/current.json').then(function (response) {
            if (response.ok) {
                return response.json();
            } else {
                return Promise.reject(response);
            }
        });
    };

    var updateElement = function (selector, content) {
        var element = document.querySelector(selector);
        if (element) {
            element.innerHTML = content;
            element.classList.remove('loading');
        }
    };

    var updateImage = function (selector, src) {
        var element = document.querySelector(selector);
        if (element) {
            element.src = src;
            element.classList.remove('loading');
        }
    };

    var formatPower = function (power) {
        if (power >= 1000) {
            return (power / 1000).toFixed(2) + ' kW';
        }
        return Math.round(power) + ' W';
    };

    var formatTime = function (minutes) {
        var hours = Math.floor(minutes / 60);
        var mins = minutes % 60;
        return hours + 'h ' + mins + 'm';
    };

    return {
        init: async function () {
            try {
                // Fetch all energy data
                var energyData = await fetchEnergyData();
                var zoeData = await fetchZoeData();
                var houseData = await fetchHouseTempData();
                
                EnergyDashboard.updateAll(energyData, zoeData, houseData);
                
                // Initialize charts
                EnergyDashboard.initializeCharts();
                
                // Set up periodic updates
                setInterval(EnergyDashboard.refreshData, 30000); // Update every 30 seconds
                
            } catch (error) {
                console.error('Error initializing energy dashboard:', error);
            }
        },

        updateAll: function (energyData, zoeData, houseData) {
            if (energyData) {
                this.updatePVSystem(energyData);
                this.updateHouseConsumption(energyData);
                this.updateBatteryStatus(energyData);
                this.updateGridStatus(energyData);
                this.updateOverallStatus(energyData);
            }
            
            if (zoeData) {
                this.updateEVStatus(zoeData);
            }
            
            if (houseData) {
                this.updateHouseTemp(houseData);
            }
        },

        updatePVSystem: function (data) {
            // PV with Battery
            if (data.pv_battery) {
                updateElement('#pv-battery .current-power', Math.round(data.pv_battery.current_power || 0));
                updateElement('#pv-battery .battery-level', data.pv_battery.battery_level || 0);
                updateElement('#pv-battery .daily-kwh', (data.pv_battery.daily_production || 0).toFixed(2));
            }

            // PV Direct
            if (data.pv_direct) {
                updateElement('#pv-direct .current-power', Math.round(data.pv_direct.current_power || 0));
                updateElement('#pv-direct .daily-kwh', (data.pv_direct.daily_production || 0).toFixed(2));
                updateElement('#pv-direct .export-w', Math.round(data.pv_direct.export_power || 0));
            }
        },

        updateHouseConsumption: function (data) {
            if (data.house_consumption) {
                updateElement('#house-consumption-value .loading', Math.round(data.house_consumption.current_power || 0));
                updateElement('#house-daily-consumption .daily-kwh', (data.house_consumption.daily_consumption || 0).toFixed(2));
            }
        },

        updateBatteryStatus: function (data) {
            if (data.battery) {
                updateElement('#battery-status-value .loading', data.battery.level || 0);
                updateElement('#battery-charge-rate .charge-w', Math.round(data.battery.charge_rate || 0));
            }
        },

        updateGridStatus: function (data) {
            if (data.grid) {
                var gridPower = data.grid.import_power || 0;
                updateElement('#grid-status-value .loading', Math.round(gridPower));
                updateElement('#grid-cost-info .cost-cents', data.grid.cost_cents || 0);
            }
        },

        updateOverallStatus: function (data) {
            var totalProduction = (data.pv_battery?.current_power || 0) + (data.pv_direct?.current_power || 0);
            var totalConsumption = data.house_consumption?.current_power || 0;
            
            updateElement('#total-consumption-number', Math.round(totalConsumption));
            
            if (totalProduction > totalConsumption) {
                updateElement('#overall-status', 'Energieüberschuss');
                updateElement('#flow-text', 'Einspeisung');
                updateImage('#flow-indicator', '/static/img/energy/arrow_right.svg');
            } else {
                updateElement('#overall-status', 'Netzbezug');
                updateElement('#flow-text', 'Bezug');
                updateImage('#flow-indicator', '/static/img/energy/arrow_right.svg');
            }
        },

        updateEVStatus: function (data) {
            if (data.battery) {
                updateElement('#ev-model', data.model || 'Renault Zoe');
                updateElement('#ev-connection-status', data.connected ? 'Verbunden' : 'Getrennt');
                updateElement('#ev-battery-level', data.battery.level || 0);
                updateElement('#ev-range .range-km', data.battery.range || 0);
                
                if (data.charging) {
                    updateElement('#ev-charging-status', 'Lädt');
                    updateElement('#ev-charge-power .charge-kw', (data.charging.power || 0).toFixed(1));
                    updateElement('#ev-charge-time .hours-min', formatTime(data.charging.time_to_full || 0));
                } else {
                    updateElement('#ev-charging-status', 'Nicht am Laden');
                    updateElement('#ev-charge-power .charge-kw', '0.0');
                    updateElement('#ev-charge-time .hours-min', '--');
                }
            }
        },

        updateHouseTemp: function (data) {
            if (data.temperature) {
                // Could add indoor temperature display later if needed
                console.log('House temperature:', data.temperature);
            }
        },

        refreshData: async function () {
            try {
                var energyData = await fetchEnergyData();
                var zoeData = await fetchZoeData();
                EnergyDashboard.updateAll(energyData, zoeData, null);
            } catch (error) {
                console.error('Error refreshing data:', error);
            }
        },

        initializeCharts: function () {
            var options = {
                series: [{
                    name: 'PV Erzeugung',
                    data: []
                }, {
                    name: 'Verbrauch',
                    data: []
                }],
                chart: {
                    type: 'area',
                    height: 200,
                    animations: {
                        enabled: false
                    }
                },
                xaxis: {
                    categories: ['00:00', '04:00', '08:00', '12:00', '16:00', '20:00', '24:00']
                },
                yaxis: {
                    title: {
                        text: 'Leistung (W)'
                    }
                },
                colors: ['#000', '#666'],
                stroke: {
                    curve: 'smooth'
                },
                fill: {
                    type: 'gradient',
                    gradient: {
                        shadeIntensity: 1,
                        inverseColors: false,
                        opacityFrom: 0.7,
                        opacityTo: 0.3
                    }
                },
                tooltip: {
                    theme: 'light'
                },
                legend: {
                    show: true,
                    position: 'top'
                }
            };

            var chart = new ApexCharts(document.querySelector("#energy-chart-container"), options);
            chart.render();
            
            // Store chart instance for updates
            this.energyChart = chart;
        }
    };
})();

document.addEventListener("DOMContentLoaded", function (event) {
    EnergyDashboard.init();
});