document.addEventListener("DOMContentLoaded", function () {
    fetch('/api/house/power/current.json').then(function (response) {
        if (response.ok) {
            return response.json();
        } else {
            return Promise.reject(response);
        }
    }).then(function (data) {
        new Chart(document.getElementById("chartjs-pie"), {
            type: "pie",
            data: {
                labels: ["Netzbezug", "Balkonsolar-Produktion"],
                datasets: [{
                    data: [data.house_consumption, data.solar_production],
                    backgroundColor: [
                        "#cc6600",
                        "#339933"
                    ],
                    borderColor: "transparent"
                }]
            },
            options: {
                maintainAspectRatio: false,
                legend: {
                    display: true
                }
            }
        });
    }).catch(function (err) {
        console.warn('Something went wrong.', err);
    });
});

document.addEventListener("DOMContentLoaded", function () {
    fetch('/api/house/stats/temp/current.json').then(function (response) {
        if (response.ok) {
            return response.json();
        } else {
            return Promise.reject(response);
        }
    }).then(function (data) {
        document.getElementById("temperature-outside").textContent = data.temperature_outside;
    }).catch(function (err) {
        console.warn('Something went wrong.', err);
    });
});
