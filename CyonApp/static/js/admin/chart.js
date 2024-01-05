function drawDoughnutChart(data,labels, name) {
    const chart = document.getElementById(`${name}`).getContext('2d')
            new Chart(chart, {
                type: 'doughnut',
                data: {
                  labels: labels,
                  datasets: [{
                    label: 'Doanh thu',
                    data: data,
                    borderWidth: 1
                  }]
                },
                options: {
                      scales: {
                            y: {
                              beginAtZero: true
                            }
                      }
                }
              });
}

function drawBarChart(data,labels, name) {
    const chart = document.getElementById(`${name}`).getContext('2d')
            new Chart(chart, {
                type: 'bar',
                data: {
                  labels: labels,
                  datasets: [{
                    label: "tần suất",
                    data: data,
                    borderWidth: 1
                  }]
                },
                options: {
                      scales: {
                            y: {
                              beginAtZero: true
                            }
                      }
                }
              });
}