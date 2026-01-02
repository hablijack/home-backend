var Weatherstation = (function () {

    var fetchWeatherData = function () {
        return fetch('/api/weather').then(function (response) {
            if (response.ok) {
                return response.json();
            } else {
                return Promise.reject(response);
            }
        });
    };

    var fetchOpenMeteoData = function () {
        return fetch('/api/openmeteo').then(function (response) {
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

    var formatTime = function (timestamp) {
        if (!timestamp) return '';
        
        var date = new Date(timestamp);
        var hours = date.getHours().toString().padStart(2, '0');
        var minutes = date.getMinutes().toString().padStart(2, '0');
        return hours + ':' + minutes;
    };

    var formatDayName = function (timestamp) {
        if (!timestamp) return '';
        
        var date = new Date(timestamp);
        var days = ['Sonntag', 'Montag', 'Dienstag', 'Mittwoch', 'Donnerstag', 'Freitag', 'Samstag'];
        return days[date.getDay()];
    };

    

    return {
        init: async function () {
            var weatherData = await fetchWeatherData();
            var openMeteoData = await fetchOpenMeteoData();
            Weatherstation.updateAll(weatherData, openMeteoData);
        },

        updateCurrentWeather: function (data) {
            var weather = data["weather"][0];
            
            // Update current outside temperature
            updateElement('#current-outside .min-temp .temp-value', weather["min_temp"]);
            updateElement('#current-outside .max-temp .temp-value', weather["max_temp"]);
            
            // Update condition image and name
            updateImage('#condition-image', "/static/img/weather/weather_icons/" + weather["icon"]);
            updateElement('#condition-name', weather["condition"]);
            
            // Update precipitation
            updateElement('#current-prec-perc-value', weather["prec_prob"]);
            updateElement('#current-prec-value', weather["prec_amount"] + weather["prec_text"]);

            // Update sunrise and sunset times
            if (weather["sunrise"]) {
                updateElement('#sunrise-text', formatTime(weather["sunrise"]));
            }
            if (weather["sunset"]) {
                updateElement('#sunset-text', formatTime(weather["sunset"]));
            }
        },

        updateForecast: function (data) {
            var forecasts = data["weather"].slice(1, 6); // Get next 5 days
            var forecastCards = document.querySelectorAll('.forecast-card');
            
            forecasts.forEach(function (forecast, index) {
                if (forecastCards[index]) {
                    var card = forecastCards[index];
                    
                    // Update headline (day name)
                    updateElementInCard(card, '.forecast-headline', formatDayName(forecast.day * 1000) || 'Tag ' + (index + 1));
                    
                    // Update condition image
                    updateImageInCard(card, '.forecast-image', "/static/img/weather/weather_icons/" + forecast.icon);
                    
                    // Update condition text
                    updateElementInCard(card, '.condition-text', forecast.condition);
                    
                    // Update temperatures
                    updateElementInCard(card, '.min-forecast .temp-value', forecast.min_temp);
                    updateElementInCard(card, '.max-forecast .temp-value', forecast.max_temp);
                    
                    // Update precipitation
                    updateElementInCard(card, '.prec-forecast .prec-value', forecast.prec_prob);
                    updateElementInCard(card, '.prec-perc-forecast .prec-perc-value', forecast.prec_amount);
                }
            });
        },

        updateAll: function (data, openMeteoData) {
            this.updateCurrentWeather(data);
            this.updateForecast(data);
            this.updateOpenMeteoData(openMeteoData, data);
        },

        updateUVIndex: function (uvIndex) {
            var uvNumber = document.querySelector('#uv-index-number');
            var uvLabel = document.querySelector('#uv-index-label');
            
            if (uvNumber && uvLabel) {
                uvNumber.innerHTML = uvIndex.toFixed(1);
                uvNumber.classList.remove('loading');
                
                // Determine UV index level and apply appropriate styling
                var level = '';
                var cssClass = '';
                
                if (uvIndex <= 2) {
                    level = 'Low';
                    cssClass = 'uv-low';
                } else if (uvIndex <= 5) {
                    level = 'Moderate';
                    cssClass = 'uv-moderate';
                } else if (uvIndex <= 7) {
                    level = 'High';
                    cssClass = 'uv-high';
                } else if (uvIndex <= 10) {
                    level = 'Very High';
                    cssClass = 'uv-very-high';
                } else {
                    level = 'Extreme';
                    cssClass = 'uv-extreme';
                }
                
                uvLabel.innerHTML = level;
                uvLabel.className = 'uv-index-label ' + cssClass;
            }
        },

        updateOpenMeteoData: function (data, weatherData) {
            if (data && data.weather && data.weather.current) {
                var current = data.weather.current;
                
                // Update current outside temperature
                if (current.temperature !== undefined && current.temperature !== null) {
                    updateElement('#current-outside .temperature', Math.round(current.temperature));
                }
                
                // Update humidity
                if (current.humidity !== undefined && current.humidity !== null) {
                    updateElement('#current-outside .humidity', Math.round(current.humidity));
                }
                
                // Update feels like temperature
                if (current.feels_like !== undefined && current.feels_like !== null) {
                    updateElement('#feels-like-value .loading', Math.round(current.feels_like));
                }
                
                // Update UV index if available
                if (current.uv_index !== undefined && current.uv_index !== null && current.uv_index > 0) {
                    this.updateUVIndex(current.uv_index);
                } else if (data.weather.daily && data.weather.daily.uv_index_max) {
                    // Fallback to daily max UV index
                    this.updateUVIndex(data.weather.daily.uv_index_max);
                }
            }
            
            // Update moon phase with API data
            this.updateMoonPhase(weatherData);
        },

        updateMoonPhase: function (weatherData) {
            // Use moon phase data from API instead of calculating it
            if (weatherData && weatherData.weather && weatherData.weather[0]) {
                var currentWeather = weatherData.weather[0];
                var moonPhaseIndex = currentWeather.moon_phase_index || 0;
                var moonPhaseName = currentWeather.moon_phase_name || 'Neumond';
                
                // Update moon phase text
                updateElement('#moon-phase-text', moonPhaseName);
                
                // Update moon phase icon
                updateImage('.moon-icon', '/static/img/moon_phase/' + moonPhaseIndex + '.svg');
            }
        }
    };

    function updateElementInCard(card, selector, content) {
        var element = card.querySelector(selector);
        if (element) {
            element.innerHTML = content;
            element.classList.remove('loading');
        }
    }

    function updateImageInCard(card, selector, src) {
        var element = card.querySelector(selector);
        if (element) {
            element.src = src;
            element.classList.remove('loading');
        }
    }
})();

document.addEventListener("DOMContentLoaded", function (event) {
    Weatherstation.init();
});
