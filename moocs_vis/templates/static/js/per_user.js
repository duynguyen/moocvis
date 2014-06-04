var width = 1300,
    height = 2000;

var radius = 15; /* radius of circles */
var d3LineLinear = d3.svg.line().interpolate("linear");
var d3color = d3.interpolateRgb("#BAE4B3", "#006D2C"); /* color range for flow lines */
var node = [], force, graphLength = 0, indicators;

var graph;

var lecture = $('#lecture_q').val();
var user = $('#user_q').val();
var seq;
updateSeq();
reloadIndicators(lecture);
var keys = [];

// init value
$('input[name="playrate_q"]:first').attr('checked', 'checked');
$('input[name="playrate_q"]:first').parent().toggleClass("success");

$.each(indicators.indicators, function(i, k) {
  $("#select_indicator").append("<option value='" + k + "'>" + k + "</option>");
});

drawGraph(lecture, user);

$(".toggle-btn input[type=radio]").change(function() {
    if($(this).attr("name")) {
        $(this).parent().addClass("success").siblings().removeClass("success")
    } else {
        $(this).parent().toggleClass("success");
    }
    updateUserList();
});

$('#lecture_q').on('change', function() {
  lecture = $(this).val();
  reloadIndicators(lecture);
  updateUserList();
});

$('#select_indicator').on('change', function() {
  updateUserList();
  $('#indicator_option').removeClass('invisible');
});

$("#toggle_legend").click(function() {
  $("#legend_img").slideToggle("slow");
});

function reloadIndicators(lecture) {
  $.ajax({
    dataType: "json",
    url: "/indicators/json/?lecture=" + lecture,
    async: false,
    success: function(data){ indicators = data; }
  });
}

function updateSeq() {
  if($('input[name="seq_q"]:checked').length == 0) {
    seq = 'time_seq';
  } else {
    seq = $('input[name="seq_q"]:checked').val();
  }
}

function updateUserList() {
  $('#indicator_option').html('');
  updateSeq();
  var playrate = $('input[name="playrate_q"]:checked').val();
  var userList = indicators[$("#select_indicator").val() + '-' + playrate];
  $.each(userList, function(i, d) {
    $('#indicator_option').append("<a href='/per-user/?lecture_q=" + lecture + "&seq_q=" + seq +
      "&user_q=" + d + "&playrate_q=" + playrate + "'>" + d + "</a><br>");
  });
}

function drawGraph(lecture, user) {

  graph = getGraph(lecture, user);
  var nodes = graph["nodes"];
      circles = graph["circles"];
      line_links = graph["line_links"];

  var topOffset = 50;
      leftOffset = 50;
      nodeDistance = (width - leftOffset) / nodes.length;

  $.each(circles, function(i, d) {
      if(d.y > graphLength) {
          graphLength = d.y;
      }
  });
  graphLength *= 50

  height = graphLength + topOffset + 150;
  $('#vis').html('');
  var svg = d3.select("#vis").append("svg").attr("width", width).attr("height", height);
  var tooltipDiv = d3.select("body").append("div")   // declare the properties for the div used for the tooltips
              .attr("class", "tooltip")       // apply the 'tooltip' class
              .style("opacity", 0);           // set the opacity to nil

  for(var i = 0; i < nodes.length; i++) {
    element = nodes[i];
    element.pos = [(element.name - 1) * nodeDistance + leftOffset, topOffset];
  }
  node = svg.selectAll(".node");

  force = d3.layout.force()
                         .charge(-400)
                         // .linkDistance(300)
                         .size([width, height])
                         // .links(links)
                         .nodes(nodes);
                         // .on("tick", tick);

  //GLOBAL STRENGTH SCALE
  var strength_scale = d3.scale.linear().range([2, 4]) /* thickness range for flow lines */
  .domain([0, d3.max(line_links, function(d) {
      return 5;
  })]);

  var color_scale = d3.scale.linear().range([0, 1]).domain([0, d3.max(line_links, function(d) {
      return 5;
  })]);

  //SHADOW DEFINITION
  createDefs(svg.append('svg:defs'));

  function createDefs(defs) {
      var dropShadowFilter = defs.append('svg:filter').attr('id', 'dropShadow');
      dropShadowFilter.append('svg:feGaussianBlur').attr('in', 'SourceAlpha').attr('stdDeviation', 1);
      dropShadowFilter.append('svg:feOffset').attr('dx', 0).attr('dy', 1).attr('result', 'offsetblur');
      var feMerge = dropShadowFilter.append('svg:feMerge');
      feMerge.append('svg:feMergeNode');
      feMerge.append('svg:feMergeNode').attr('in', "SourceGraphic");
  }

  drawRuler();
  drawTopNodes();

  $.each(circles, function(i, d) {
      var node = svg.append("g").attr("class", "gnode");
      // var r = nodeDistance * (d.type == 'virtual' ? radius / 2 : radius) / 100
      var r = (d.type == 'virtual' ? radius / 2 : (d.type == 'dest' ? radius / 1.5 : radius));
      // var textMargin = d.type == 'ratechange' ? r / 2 : 0;
      node.append("circle")
          .attr('filter', 'url(#dropShadow)')
          .attr("class", "circle")
          .attr("id", "circle" + d.name)
          .attr("r", r)
          .attr("cx", (d.x - 1) * nodeDistance + leftOffset + nodeDistance * 3 / 10)
          .attr("cy", (d.y + 1) * 50 + topOffset * 1.5)
          .style("fill", function() {
            if(d.type == 'seeked') return 'black';
            else if(d.type == 'pause') return 'red';
            else if(d.type == 'ratechange') return '#bbb';
            else if(d.type == 'dest') return 'black';
            else return 'grey';
          })
          .style("fill-opacity", d.type == 'seek' ? 1 : 0.8);

      if(d.type == 'ratechange' && d.rate - d.prev_rate > 0) {
        node.append("image")
          .attr("xlink:href", "/static/img/up.png")
          .attr("x", (d.x - 1) * nodeDistance + leftOffset + nodeDistance * 3 / 10 - r / 3)
          .attr("y", (d.y + 1) * 50 + topOffset * 1.5 - r - 2)
          .attr("width", r / 1.5)
          .attr("height", r);
      }
      if(d.type == 'ratechange' && d.rate - d.prev_rate < 0) {
        node.append("image")
          .attr("xlink:href", "/static/img/down.png")
          .attr("x", (d.x - 1) * nodeDistance + leftOffset + nodeDistance * 3 / 10 - r / 3)
          .attr("y", (d.y + 1) * 50 + topOffset * 1.5 + 2)
          .attr("width", r / 1.5)
          .attr("height", r);
      }
      
      node.append("text")
          .attr("text-anchor", "middle")
          .attr("dx", (d.x - 1) * nodeDistance + leftOffset + nodeDistance * 3 / 10)
          .attr("dy", (d.y + 1) * 50 + topOffset * 1.5 + r / 4)
          .text(d.time)
          .attr("font-size", "10px")
          .style("fill", "white");
      node.on("mouseover", function() {
            var pageX = d3.mouse(this)[0];
            var pageY = d3.mouse(this)[1];
            // $("#slide").html('<img src=slide_img/week' + lecture + '_' + d.slide + '.png />');
            var additionalText = d.type == 'pause' ? 'Pause in ' + d.duration + ' seconds'
            : (d.rate ? "Change rate: " + d.prev_rate + " ---> " + d.rate : '')
            tooltipDiv.transition()                                    // declare the transition properties to bring fade-in div
                    .duration(50)                                  // it shall take 200ms
                    .style("opacity", .9);                          // and go all the way to an opacity of .9
                  tooltipDiv.html(additionalText)  // add the text of the tooltip as html 
                    .style("left", (pageX < (width - 300) ? pageX : (width - 300)) + "px")         // move it in the x direction 
                    .style("top", (pageY > 100 ? (pageY - 10) : 10) + "px")    // move it in the y direction
                    .style("background-image","url(" + nodes[d.x - 1]['image_url'] + ")")
                    .style("background-size","contain")
                    .style("background-repeat","no-repeat");
          })
          .on("mouseout", function() {
            tooltipDiv.transition()                                    // declare the transition properties to fade-out the div
              .duration(100)                                  // it shall take 500ms
              .style("opacity", 0);
          });
  });

  svg.selectAll(".link_line").data(line_links).enter().append("path").attr("class", "link_line")
  .attr("fill", function(d) {
      if(d.group == 'BW') return 'red';
      else if((d.group == 'FW')) return 'green';
      else if((d.group == 'cBW')) return '#fa8072';
      else if((d.group == 'cFW')) return '#7fff00';
      else return '#000';
  })
  .attr("fill-opacity", function(d) {
      if(d.group == 'v' || d.group == 'cBW' || d.group == 'cFW') return 0.7;
  })
  .attr("id", function(i, d) {
      return "link_line" + d;
  })
  .attr("d", function(d) {
      return drawCurve(d);
  });

  function getGraph(lecture, user) {
    var graph;
    $.ajax({
      dataType: "json",
      url: "lecture-json?user=" + user + "&lecture=" + lecture + "&seq=" + seq,
      async: false,
      success: function(data){ graph = data; }
    });
    return graph;
  }

  function drawTopNodes() { 
    //Add nodes with texts in them
    node = node.data(force.nodes());
    node.enter().append("g").attr("class", "topnode");
    node.append("rect")
        .attr("class", function(d) { return "node group" + d.group })
        .attr("x", function(d) { return d.pos[0]; })
        .attr("y", function(d) { return d.pos[1] - nodeDistance * 2 / 10; })
        .attr("width", nodeDistance * 6 / 10)
        .attr("height", nodeDistance * 4 / 10)
        .style("fill", function(d) { if(d.type=='q') return "orange"; else if(d.type=='d') return "skyblue"; else return "beige" });
    node.append("text")
        .attr("text-anchor", "middle")
        .attr("x", function(d) { return d.pos[0] + nodeDistance * 3 / 10; })
        .attr("y", function(d) { return d.pos[1] + 3; })
        .text(function(d) { return d.slide; })
        .attr("font-size", (nodeDistance / 7) + "px")
        .attr("font-weight", "bold")
        .style("fill", "black");
      // source or target properties match the hovered node.
    node.on("mouseover", function(d) {
            var pageX = d3.mouse(this)[0];
            var pageY = d3.mouse(this)[1];
            // $("#slide").html('<img src=slide_img/week' + lecture + '_' + d.slide + '.png />');
            tooltipDiv.transition()                                    // declare the transition properties to bring fade-in div
                    .duration(50)                                  // it shall take 200ms
                    .style("opacity", .9);                          // and go all the way to an opacity of .9
                  tooltipDiv.html('')  // add the text of the tooltip as html 
                    .style("left", (pageX < (width - 300) ? pageX : (width - 300)) + "px")         // move it in the x direction 
                    .style("top", (pageY > 100 ? (pageY - 10) : 10) + "px")    // move it in the y direction
                    .style("background-image","url(" + d.image_url + ")")
                    .style("background-size","contain")
                    .style("background-repeat","no-repeat");
          })
          .on("mouseout", function() {
            tooltipDiv.transition()                                    // declare the transition properties to fade-out the div
              .duration(100)                                  // it shall take 500ms
              .style("opacity", 0);
          });

    node.exit().remove();

    force.start();
  }

  function drawRuler(){

      for(var i in nodes) {
          var mynode = nodes[i];
          svg.append("line")
              .attr("class", "vertical_ruler")
              .attr("x1", mynode.pos[0] + nodeDistance * 3 / 10)
              .attr("y1", 5 + topOffset)
              .attr("x2", mynode.pos[0] + nodeDistance * 3 / 10)
              .attr("y2", graphLength + topOffset + 150)
              .attr("stroke-width", 1)
              .attr("stroke-opacity", 0.7)
              .attr("stroke", "#999");
      }
  }

  function drawCurve(d) {
      var slope = Math.atan2((+d3.select('#circle' + d.target).attr("cy") - d3.select('#circle' + d.source).attr("cy")), (+d3.select('#circle' + d.target).attr("cx") - d3.select('#circle' + d.source).attr("cx")));
      var slopePlus90 = Math.atan2((+d3.select('#circle' + d.target).attr("cy") - d3.select('#circle' + d.source).attr("cy")), (+d3.select('#circle' + d.target).attr("cx") - d3.select('#circle' + d.source).attr("cx"))) + (Math.PI / 2);

      var sourceX = +d3.select('#circle' + d.source).attr("cx");
      var sourceY = +d3.select('#circle' + d.source).attr("cy");
      var targetX = +d3.select('#circle' + d.target).attr("cx");
      var targetY = +d3.select('#circle' + d.target).attr("cy");

      var arrowOffset = 10;
      var points = [];
      points.push([sourceX + radius * Math.cos(slope) - strength_scale(5) * Math.cos(slopePlus90), sourceY + radius * Math.sin(slope) - strength_scale(5) * Math.sin(slopePlus90)]);
      points.push([sourceX + radius * Math.cos(slope), sourceY + radius * Math.sin(slope)]);
      points.push([targetX - radius * Math.cos(slope), targetY - radius * Math.sin(slope)]);
      points.push([targetX - (radius + arrowOffset) * Math.cos(slope) - strength_scale(5 + (arrowOffset * 1.5)) * Math.cos(slopePlus90), targetY - (radius + arrowOffset) * Math.sin(slope) - strength_scale(5 + (arrowOffset * 1.5)) * Math.sin(slopePlus90)]);
      points.push([targetX - (radius + arrowOffset) * Math.cos(slope) - strength_scale(5) * Math.cos(slopePlus90), targetY - (radius + arrowOffset) * Math.sin(slope) - strength_scale(5) * Math.sin(slopePlus90)]);
    return d3LineLinear(points) + "Z";
  }
}