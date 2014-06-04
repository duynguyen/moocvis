// var lecturesData;

// $.ajax({
//     dataType: "json",
//     url: "json?course_id=1",
//     async: false,
//     success: function(data){ lecturesData = data; }
// });

$(".toggle-btn input[type=radio]:first").attr('checked', 'checked');
$('input[name="playrate_q"]:first').parent().toggleClass("success");

$("#select_indicator").on('change', function() {
    redraw();
});

$(".toggle-btn input[type=radio]").change(function() {
    if($(this).attr("name")) {
        $(this).parent().addClass("success").siblings().removeClass("success")
    } else {
        $(this).parent().toggleClass("success");
    }
    redraw();
});


$('.vis-container').css('width', $(window).width() - 100);
$('#container').css('width', 3500);
$('#container').css('height', 800);
redraw();

function redraw() {
    var option = $("#select_indicator").val();
    var rate = $('input[name="playrate_q"]:checked').val();
    var key = option + '-' + rate;
    var data = lecturesData.data[key].data;
    labels = {
        enabled: true,
        formatter: function() {
            return 'sad';
        }
    }
    $.each(data, function(i,d) {
        d['dataLabels'] = labels;
    });
    $('#container').html('');
    $('#container').highcharts({
        chart: {
            type: 'bubble',
            zoomType: 'xy'
        },

        legend: {
            enabled: false
        },

        title: {
            text: ''
        },

        subtitle: {
            text: 'Click on a bubble to view details about lecture'
        },

        plotOptions: {
            bubble: {
                dataLabels: {
                    enabled: true,
                    style: { textShadow: 'none' },
                    formatter: function() {
                        return this.point.week;
                    }
                },
                minSize: '2%',
                maxSize: '8%'
            },
            series: {
                cursor: 'pointer',
                point: {
                    events: {
                        click: function() {
                            location.href = '/per-user/?lecture_q=' + this.options.name
                            + "&user_q=" + this.series.name + "&playrate_q=" + rate;
                        }
                    }
                },
            }
        },

        tooltip: {
            formatter: function() {
                return 'User <b>' + this.series.name + '</b><br>Lecture <b>' + this.point.name + '</b><br>Corresponding behaviors count: <b>' + this.point.z + '</b>';
            }
        },

        xAxis: {
            categories: lecturesData['weeks'],
            opposite: true,
            minTickInterval: 1,
            min: 0,
        },

        yAxis: {
            floor: 0,
            min: -0.5,
            // max: 2.5,
            startOnTick: false,
            endOnTick: false,
            categories: lecturesData.data[key]['users'],
            title: 'Users',
            reversed: true
        },
        series: data
        // [{
        //     dataLabels: {
        //         enabled: true,
        //         formatter:function() {
        //             return '';
        //         },
        //     },
        //     data: lecturesData.data[key].data,
        // }]
    });
}