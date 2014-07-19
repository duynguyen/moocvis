// var lecturesData;

// $.ajax({
//     dataType: "json",
//     url: "json?course_id=1",
//     async: false,
//     success: function(data){ lecturesData = data; }
// });

var option, rate, key;
var screenwidth = $(window).width() - 100;

$(".toggle-btn input[type=radio]:first").attr('checked', 'checked');
$('input[name="playrate_q"]:first').parent().toggleClass("success");

$("#select_indicator").on('change', function() {
    drawAll();
});

$(".toggle-btn input[type=radio]").change(function() {
    if($(this).attr("name")) {
        $(this).parent().addClass("success").siblings().removeClass("success")
    } else {
        $(this).parent().toggleClass("success");
    }
    drawAll();
});

$(".toggle-btn input[name='screen']").change(function() {
    if($(this).attr("name")) {
        $(this).parent().addClass("success").siblings().removeClass("success")
    } else {
        $(this).parent().toggleClass("success");
    }
    if($("input[name='screen']:checked").val() == "full") {
        screenwidth = $(window).width() - 100;
    } else {
        screenwidth = 3500;
    }
    drawAll();
});

$("#search_user_btn").on("click", function() {
    $.ajax({
        dataType: "json",
        url: "/lectures/user/json?course_id=1&user_id=" + $("#user_id").val(),
        async: false,
        success: function(data){
            redraw(data, [$("#user_id").val()]);
        }
    });
});

$('.vis-container').css('width', $(window).width() - 100);
$('#container').css('height', 800);
drawAll();

function drawAll() {
    option = $("#select_indicator").val();
    rate = $('input[name="playrate_q"]:checked').val();
    key = option + '-' + rate;
    redraw(lecturesData.data[key].data, lecturesData.data[key]['users']);
}

function redraw(data, yAxis) {
    $('#container').css('width', screenwidth);
    labels = {
        enabled: true,
        formatter: function() {
            return '';
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
            min: 0,
            startOnTick: false,
            endOnTick: false,
            categories: yAxis,
            title: 'Users',
            reversed: true
        },
        series: data
    });
}