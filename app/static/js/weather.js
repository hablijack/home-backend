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
    return {
        init: async function () {
            var weatherData = await fetchWeatherData();
            Weatherstation.updateCurrentOutside(weatherData);
        },

        updateCurrentOutside: function (data) {
            document.querySelector('#current-outside .min-temp .min-temp-value').innerHTML = data["weather"][0]["min_temp"];
            document.querySelector('#current-outside .max-temp .max-temp-value').innerHTML = data["weather"][0]["max_temp"];
            document.querySelector('#condition-image').src = "/static/img/weather/weather_icons/" + data["weather"][0]["icon"];
            document.querySelector('#condition-name').innerHTML = data["weather"][0]["condition"];
            document.querySelector('#current-prec-perc-value').innerHTML = data["weather"][0]["prec_prob"];
            document.querySelector('#current-prec-value').innerHTML = data["weather"][0]["prec_amount"] + data["weather"][0]["prec_text"];
        },
    };
})();

document.addEventListener("DOMContentLoaded", function (event) {
    Weatherstation.init();
});
