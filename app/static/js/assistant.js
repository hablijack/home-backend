var Frontend = (function () {

  var drawZoeChart = function (data) {
    var options = {
      series: [data.battery_level],
      chart: {
        height: 150,
        type: "radialBar",
        offsetY: 0,
      },
      colors: ['#969696'],
      plotOptions: {
        radialBar: {
          startAngle: -180,
          endAngle: 180,
          track: {
            show: false,
          },
          legend: {
            show: false,
          },
          dataLabels: {
            name: {
              offsetY: -3,
              color: "#73d8fd",
              fontSize: "17px"
            },
            value: {
              offsetY: -1,
              color: "#73d8fd",
              fontSize: "20px",
              show: true
            }
          }
        },
      },
      labels: ['ZOE'],
      stroke: {
        dashArray: 10
      },
    };

    var chart = new ApexCharts(
      document.querySelector("#zoe-fuel-chart"),
      options
    );
    chart.render();
    return chart;
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
  return {
    init: async function () {
      Frontend.updateClock();
      this.zoeChart = drawZoeChart(await fetchZoeData());

      setInterval("Frontend.updateClock()", 60000);
      setInterval("Frontend.updateZoe()", 60000)
    },

    updateClock: function () {
      document.querySelector('.clock').innerHTML = moment().locale("de").format("LLL");
    },

    updateZoe: async function() {
      var zoeData = await fetchZoeData();
      this.zoeChart.updateSeries([zoeData.battery_percent]);
    },
  };
})();

document.addEventListener("DOMContentLoaded", function(event) { 
  Frontend.init();
});
