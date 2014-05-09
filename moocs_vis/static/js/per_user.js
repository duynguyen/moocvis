var width = 1300,
    height = 2000;

var radius = 15; /* radius of circles */
var d3LineLinear = d3.svg.line().interpolate("linear");
var d3color = d3.interpolateRgb("#BAE4B3", "#006D2C"); /* color range for flow lines */
var node = [], force, graphLength = 0;

var graph;

var lecture = $('#lecture_q').val();
var user = $('#user_q').val();
var seq;
if($('input[name="seq_q"]:checked').length == 0) {
  seq = 'time_seq';
} else {
  seq = $('input[name="seq_q"]:checked').val();
}
drawGraph(lecture, user);

$('#select_indicator').on('change', function() {
  $('.indicator_option').addClass('invisible');
  $('#' + $(this).val()).removeClass('invisible');
});

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
      var r = (d.type == 'virtual' ? radius / 2 : radius)
      node.append("circle")
          .attr('filter', 'url(#dropShadow)')
          .attr("class", "circle")
          .attr("id", "circle" + d.name)
          .attr("r", r)
          .attr("cx", (d.x - 1) * nodeDistance + leftOffset + nodeDistance * 3 / 10)
          .attr("cy", (d.y + 1) * 50 + topOffset * 1.5)
          .style("fill", function() {
            if(d.type == 'seek') return 'black';
            else if(d.type == 'pause') return 'red';
            else return 'grey';
          })
          .style("fill-opacity", d.type == 'seek' ? 1 : 0.8);
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
            tooltipDiv.transition()                                    // declare the transition properties to bring fade-in div
                    .duration(50)                                  // it shall take 200ms
                    .style("opacity", .9);                          // and go all the way to an opacity of .9
                  tooltipDiv.html(d.duration ? 'Pause in ' + d.duration + ' seconds' : '')  // add the text of the tooltip as html 
                    .style("left", (pageX < (width - 300) ? pageX : (width - 300)) + "px")         // move it in the x direction 
                    .style("top", (pageY > 100 ? (pageY - 10) : 10) + "px")    // move it in the y direction
                    .style("background-image","url(" + nodes[d.x]['image_url'] + ")")
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
      if(d.group == 'r') return 'red';
      else if((d.group == 'd')) return 'green';
      else return 'orange';
  })
  .attr("fill-opacity", function(d) {
      if(d.group == 'v') return 0.4;
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