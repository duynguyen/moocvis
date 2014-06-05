var lecturesData;

$.ajax({
    dataType: "json",
    url: "json?course_id=1",
    async: false,
    success: function(data){ lecturesData = data; }
});

var options;
$.each(lecturesData.events, function(i, e) {
    options += "<option value='" + e + "'>" + e + "</option>";
});
$("#option").html(options);

$("#option").on('change', function() {
    redraw($(this).val());
});

$('#container').css('width', $(window).width() - 50);
$('#container').css('height', 800);
redraw('all');

function redraw(option) {
    $('#container').html('');
    $('#container').highcharts({
        chart: {
            type: 'bubble',
            zoomType: 'xy'
        },

        title: {
            text: ''
        },

        subtitle: {
            text: 'Click on a bubble to view clickstream details about lecture'
        },

        plotOptions: {
            bubble: {
                dataLabels: {
                    enabled: true,
                    style: { textShadow: 'none' },
                    formatter: function() {
                        return this.point.name;
                    }
                },
                minSize: '2%',
                maxSize: '13%'
            },
            series: {
                cursor: 'pointer',
                point: {
                    events: {
                        click: function() {
                            location.href = '/per-lecture/?lecture_q=' + this.options.name;
                        }
                    }
                },
            }
        },

        tooltip: {
            formatter: function() {
                return 'Lecture <b>' + this.point.name + '</b><br>Corresponding behaviors count: ' + this.point.z;
            }
        },

        xAxis: {
            // categories: ['Project 1', 'Project 2', 'Project 3', 'Project 4'],
            opposite: true,
            minTickInterval: 1,
        },

        yAxis: {
            floor: 0,
            min: -0.5,
            // max: 2.5,
            startOnTick: false,
            endOnTick: false,
            categories: lecturesData.weeks,
            title: 'Course',
            reversed: true
        },
        series: lecturesData.data[option]
    });
}