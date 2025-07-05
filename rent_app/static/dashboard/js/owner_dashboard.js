$(function () {
    // Revenue graph
    var options_revenue_graph = {
        series: [{
            name: 'Revenue',
            data: window.monthlyRevenue
        }],
        chart: {
            type: "bar",
            height: 275,
            toolbar: {
                show: false,
            },
            foreColor: "#adb0bb",
            fontFamily: "inherit",
            sparkline: {
                enabled: false,
            },
        },
        grid: {
            show: false,
            borderColor: "transparent",
            padding: {
                left: 0,
                right: 0,
                bottom: 0,
            },
        },
        plotOptions: {
            bar: {
                horizontal: false,
                columnWidth: "25%",
                endingShape: "rounded",
                borderRadius: 5,
            },
        },
        colors: ["var(--bs-primary)"],
        dataLabels: {
            enabled: false,
        },
        yaxis: {
            show: true,
            min: 0,
            max: 500000,  // Adjust based on your revenue range
            tickAmount: 5,
            labels: {
                formatter: function (value) {
                    return '₹' + value;
                }
            }
        },
        stroke: {
            show: true,
            width: 5,
            lineCap: "butt",
            colors: ["transparent"],
        },
        xaxis: {
            type: "category",
            categories: window.months,
            axisBorder: {
                show: false,
            },
        },
        fill: {
            opacity: 1,
        },
        tooltip: {
            theme: "dark",
            enabled: true,
            y: {
                formatter: function (value) {
                    return '₹' + value.toFixed(2);
                }
            },
            x: {
                show: true
            }
        },
        legend: {
            show: false,
        },
    };

    var chart_revenue = new ApexCharts(
        document.querySelector("#revenue-graph"),
        options_revenue_graph
    );
    chart_revenue.render();
});