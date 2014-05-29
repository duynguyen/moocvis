var width = 1280, height = 680,
    arrowBone = 250,
    color = d3.scale.category20(),
    normalOpacity = 0.2,
    lectureDict = {},
    numSlides = -1,
    maxStrength = 0,
    specLevel = 0;


var svg, graph, percent, force, node, link;
    nodes = [], links = [];

var tooltipDiv = d3.select("#compare-dialog").append("div")   // declare the properties for the div used for the tooltips
            .attr("class", "tooltip")       // apply the 'tooltip' class
            .style("opacity", 0);           // set the opacity to nil

reDraw($("#lecture").val());
$( "#lecture" ).change(function() {
  $("#vis").html('');
  reDraw($(this).val());
});

// drawGostraight();

$('#disp_week').click(function() {
  $("#compare-dialog").html('');
  //TODO fix this hardcode
  tooltipDiv = d3.select("#compare-dialog").append("div")   // declare the properties for the div used for the tooltips
                 .attr("class", "tooltip")       // apply the 'tooltip' class
                 .style("opacity", 0);
  drawThroughputGraph();
  drawGostraight();
  $( "#compare-dialog" ).dialog({
    width: 900,
    maxWidth: 900,
    height: 680,
    modal: true
  });
});

$( "#level_slider" ).labeledslider({
  value: specLevel,
  min: 0,
  max: 100,
  step: 5,
  slide: function(event, ui) {
    specLevel = ui.value;
    updateLink();
  }
});

$("#show_self").on("change", function() {
  updateLink();
});

function updateLink() {
  var allLinks = $(".link");
  var show = $("#show_self");
  $.each(allLinks, function(i, l) {
    var strength = parseInt(l.getAttribute("data-strength"));
    if(strength < specLevel || (!$("#show_self").is(':checked') && parseInt(l.getAttribute("data-targetname")) >= numSlides)) {
      l.setAttribute("class", "link hidden");
    } else {
      l.setAttribute("class", "link");
    }
  });
}

function reDraw(lecture) {
  $("#vis").html('');
  svg = d3.select("#vis")
          .append("svg")
          .attr("class", "vis")
          .attr("width", width)
          .attr("height", height)
          .style("border","7px solid black");
  
  percent = getPercent(lecture);
  graph = getGraph(lecture);
  nodes = graph.nodes;
  links = graph.links;

  for(var i = 0; i < nodes.length; i++) {
    var element = nodes[i];
    if(element.order > numSlides) {
      numSlides = element.order;
    }
  }
  numSlides++;

  for(var i = 0; i < links.length; i++) {
    var element = links[i];
    if(element.strength > maxStrength) {
      maxStrength = element.strength;
    }
  }

  for(var i = 0; i < nodes.length; i++) {
      var element = nodes[i];
      element.pos = [(width - 1500 / numSlides) / numSlides * element.order + 750 / numSlides, arrowBone + element.y * 150];
  }// build the arrow.
  svg.append("svg:defs").selectAll("marker")
      .data(["arrow"])//(["end"])      // Different link/path types can be defined here
    .enter().append("svg:marker")    // This section adds in the arrows
      .attr("id", String)
      .attr("viewBox", "0 -5 10 10")
      .attr("refX", 16)
      .attr("refY",-1.5)
      .attr("markerWidth", 5)
      .attr("markerHeight", 5)
      .attr("orient", "auto")
    .append("svg:path")
      // .attr("marker-end", "url(#arrow)")
      .attr("d", "M0,-5L10,-2L0,5");

  node = svg.selectAll(".node"),
  link = svg.selectAll(".link");

  force = d3.layout.force()
                   .charge(-400)
                   .linkDistance(300)
                   .size([width, height])
                   .links(links)
                   .nodes(nodes)
                   .on("tick", tick);

  drawGraph();
  drawArrow();
}

function getGraph(lecture) {
  var graph;
  $.ajax({
    dataType: "json",
    url: "lecture-json?lecture=" + $('#lecture_q').val(),
    async: false,
    success: function(data){ graph = data; }
  });
  return graph;
}

function getPercent(lecture)  
{
  percent = $('#nonclick_rate').val();
  return percent;
}

////////////////////////////////////////////////////////////////
// Function to draw topology, including nodes and links
///////////////////////////////////////////////////////////////
function drawGraph() { 
  link = link.data(force.links());
  link.enter()
      .append("path")
      .attr("marker-end", "url(#end)")
   // .insert("line", ".gnode")
      .attr("class", "link")
      .attr("data-strength", function(d) { return d.strength; })
      .attr("data-targetname", function(d) { return d.target; })
      .style("stroke", function(d) {
        if(d.type == "BW") {
          return "crimson";
        }
        else {
          return "#006D2C";
        }
      })
  // .style("stroke-dasharray" ,function(d) { if(d.target==0) return "10,10"; else return "";})
   // .style("stroke-width", function(d) { return Math.log(d.strength) * 1 / Math.log(2) + 1; })
      .style("stroke-width", function(d) {
        if(d.strength < specLevel) {
          return 0;
        }
        return d.strength * 80 / maxStrength + 1;
      });
  // .style("stroke-opacity", function(d) { return (d.lr/51)*0.1 + 0.5; });
  link.exit().remove();

  //Add nodes with texts in them
  node = node.data(force.nodes());
  node.enter().append("g").attr("class", "gnode").call(force.drag);
  node.append("circle")
      .attr("class", function(d) { return "node group" + d.type })
      .attr("r", function(d) { return 300 / numSlides; })
      .style("fill", function(d) { if(d.type=='q') return "orange"; else if(d.type=='d') return "skyblue"; else return "beige" })
      .style("fill-opacity", function(d) { if(d.y==0) return 1; else return 0; })
      .style("stroke", function(d) { if(d.y==0) return "black"; else return "none"; });
  node.append("text")
      .attr("text-anchor", "middle")
      .attr("dy", "+" + 60 / numSlides)
      .text(function(d) { return d.slide; })
      .attr("font-size", 150 / numSlides + "px")
      .attr("font-weight", "bold")
      .style("fill", "black")
      .style("fill-opacity", function(d) { if(d.y==0) return 1; else return 0; });
  // source or target properties match the hovered node.
  node.on('mouseover', function(d) {
    link.style('stroke-opacity', function(l) {
      if (d === l.source || d === l.target)
        return 0.9;
      else
        return normalOpacity;
    });
    $("#slide").html('<img src="' + d.url + '" />');
    // $("#slide").removeClass('hidden');
    var nodeData = [{orient: 'in', strength: d.in}, {orient: 'out', strength: d.out}];
    // $("#throughtput").html(d.slide);
    var maxi1 = d3.max(getThroughput('in'), function(d) { return d['in']; });
        maxi2 = d3.max(getThroughput('out'), function(d) { return d['out']; });
        maxi = (maxi1 > maxi2) ? maxi1 : maxi2;
    drawThroughput('in', d.slide, true, maxi);
    drawThroughput('out', d.slide, false, maxi);
    // $("#pie").removeClass('hidden');
  });

  // Set the stroke width back to normal when mouse leaves the node.
  node.on('mouseout', function() {
    link.style('stroke-opacity', normalOpacity);
    // $("#slide").addClass('hidden');
    $("#slide").html('');
    // $("#pie").addClass('hidden');
    $("#graph_in").html('');
    $("#graph_out").html('');
  });
  node.exit().remove();

  force.start();
}

function getThroughput(choice) {
  //slide, in, out
  dataList = [];
  for(i = 0; i < nodes.length; i++) {
    mynode = {};
    mynode['Slide'] = nodes[i].slide;
    mynode[choice] = nodes[i][choice];
    dataList.push(mynode);
  }
  return dataList;
}

function drawThroughput(choice, hovered, upside, maxi) {
  //TODO: scale by max
  var margin = {top: 10, right: 10, bottom: 10, left: 40},
      width = 590 - margin.left - margin.right,
      height = 100 - margin.top - margin.bottom;
  
  var data = [];
  for(i = 0; i < numSlides; i++) {
    var mynode = {};
    mynode['Slide'] = nodes[i].slide;
    mynode['symbol'] = nodes[i].type + (nodes[i].content_order);
    mynode[choice] = nodes[i][choice];
    data.push(mynode);
  }

  var verticalOrient = [height, 0];

  if (!upside) {
    verticalOrient = [0, height]
  }

  var x = d3.scale.ordinal()
      .rangeRoundBands([0, width], .1);

  var y = d3.scale.linear()
      .range(verticalOrient);

  var xAxis = d3.svg.axis()
      .scale(x)
      .orient("bottom");

  var yAxis = d3.svg.axis()
      .scale(y)
      .ticks(4)
      .orient("left");

 var svg = d3.select("#graph_" + choice).append("svg")
      .attr("width", width + margin.left + margin.right)
      .attr("height", height + margin.top + margin.bottom + (upside ? 20 : 0))
    .append("g")
      .attr("transform", "translate(" + margin.left + "," + margin.top + ")");

  x.domain(data.map(function(d) { return d.symbol; }));
  y.domain([0, maxi]);

  if (upside) {
    svg.append("g")
        .attr("class", "x axis")
        .attr("transform", "translate(0," + height + ")")
        .call(xAxis);
  }

  svg.append("g")
      .attr("class", "y axis")
      .call(yAxis)
    .append("text")
      .attr("transform", "rotate(-90)")
      .attr("x", upside ? 0 : (20 - height))
      .attr("y", 6)
      .attr("font-size", "12pt")
      .attr("dy", ".71em")
      .style("text-anchor", "end")
      .text(choice);

  svg.selectAll(".bar")
      .data(data)
    .enter().append("rect")
      .attr("class", "bar")
      .attr("fill-opacity", function(d) { return (hovered == d.Slide ? "0.8" : "0.3"); })
      .attr("fill", (choice == 'in') ? 'steelblue' : 'purple' )
      .attr("x", function(d) { return x(d.symbol); })
      .attr("width", x.rangeBand())
      .attr("y", function(d) { return upside ? y(d[choice]) : 0; })
      .attr("height", function(d) { return upside ? (height - y(d[choice])) : y(d[choice]); });

}

function drawArrow(lecture) {
  // Specify the path points
  var offset = percent * 1.5
  pathinfo = [{x:10, y:(arrowBone - 150)},
              {x:(width - 100), y:(arrowBone - offset)},
              {x:(width - 100), y:(arrowBone - (offset + 50))},
              {x:(width - 20), y:arrowBone},
              {x:(width - 100), y:(arrowBone + (offset + 50))},
              {x:(width - 100), y:(arrowBone + offset)},
              {x:10, y:(arrowBone + 150)}];

  // Specify the function for generating path data             
  var arrowLine = d3.svg.line()
                  .x(function(d){return d.x;})
                  .y(function(d){return d.y;})
                  .interpolate("linear"); 
                  // "linear" for piecewise linear segments

  // Creating path using data in pathinfo and path data generator
  svg.append("svg:path")
      .attr("d", arrowLine(pathinfo))
      .style("stroke-width", 4)
      .style("stroke-opacity", 0.4)
      .style("stroke", "steelblue")
      .style("fill", "none");
  svg.append("text")
      .attr("x", width - 70 )
      .attr("y",  arrowBone + 15 )
      .style("text-anchor", "middle")
      .attr("font-size", "32px")
      .attr("font-weight", "bold")
      .attr("fill-opacity", 0.4)
      .text(percent + "%");
}

function tick() {
  node.attr("transform", function(d) { return "translate(" + d.pos + ")";});
  link.attr("d", function(d) {
    // TODO Compare condition of target?!
    var dx = d.target.pos[0] - d.source.pos[0],
        dy = d.target.pos[1] - d.source.pos[1],
        dr = (d.target.name >= numSlides) ? 0 : Math.sqrt(dx * dx + dy * dy) * 0.7;
    return "M" +
              d.source.pos[0] + "," +
              d.source.pos[1] + "A" +
              dr + "," + dr + " 0 0,1 " +
              d.target.pos[0] + "," +
              d.target.pos[1];
   });
}

// Compare lectures
function drawThroughputGraph() {
  var margin = {top: 20, right: 80, bottom: 30, left: 50},
      width = 840 - margin.left - margin.right,
      height = 400 - margin.top - margin.bottom;

  var x = d3.time.scale()
      .range([0, width]);

  var y = d3.scale.linear()
      .range([height, 0]);

  var color = d3.scale.category10();

  var xAxis = d3.svg.axis()
      .scale(x)
      .orient("bottom");

  var yAxis = d3.svg.axis()
      .scale(y)
      .orient("left");

  var line = d3.svg.line()
      .interpolate("basis")
      .x(function(d) { return x(d.time); })
      .y(function(d) { return y(d.throughput); });

  var svg = d3.select("#compare-dialog").append("svg")
      .attr("width", width + margin.left + margin.right)
      .attr("height", height + margin.top + margin.bottom)
    .append("g")
      .attr("transform", "translate(" + margin.left + "," + margin.top + ")");

  var intervals;
  $.ajax({
    dataType: "json",
    url: "week-intervals",
    async: false,
    success: function(data){ intervals = data; }
  });
    color.domain(d3.keys(intervals[0]).filter(function(key) { return key !== "time"; }));

    var lectures = color.domain().map(function(name) {
      return {
        name: name,
        values: intervals.map(function(d) {
          return {time: d.time / 10, throughput: +d[name]};
        })
      };
    });

    x.domain(d3.extent(intervals, function(d) { return d.time / 10; }));

    y.domain([
      d3.min(lectures, function(c) { return d3.min(c.values, function(v) { return v.throughput; }); }),
      d3.max(lectures, function(c) { return d3.max(c.values, function(v) { return v.throughput; }); })
    ]);

    svg.append("g")
        .attr("class", "x axis")
        .attr("transform", "translate(0," + height + ")")
        .call(xAxis);

    svg.append("g")
        .attr("class", "y axis")
        .call(yAxis)
      .append("text")
        .attr("transform", "rotate(-90)")
        .attr("y", 6)
        .attr("dy", ".71em")
        .style("text-anchor", "end")
        .text("Throughput");

    var lecture = svg.selectAll(".lecture")
        .data(lectures)
      .enter().append("g")
        .attr("class", "lecture");

    lecture.append("path")
        .attr("class", "line")
        .attr("d", function(d) { return line(d.values); })
        .style("stroke", function(d) { return color(d.name); })
        .style("stroke-width", 5)
        .on("mousemove", function(d) {
          var pageX = d3.mouse(this)[0];
          var pageY = d3.mouse(this)[1];
          var relTime = x.invert(d3.mouse(this)[0]).getTime();//normalized time in the video
          var slides, lectureId = d.name;
          d3.csv("slide_changes/" + lectureId + "-slide_changes.csv", function(data) {
            var endVideo = -1;
            //get length of video
            for(var i in data) {
              var row = data[i];
              var endTime = parseInt(row.end_time);
              if(endTime > endVideo) endVideo = endTime;
            }
            for(var i in data) {
              var row = data[i];
              var startTime = parseInt(row.start_time);
              var endTime = parseInt(row.end_time);
              if(startTime / endVideo * 100 < relTime &&
                  endTime / endVideo * 100 >= relTime) {
                tooltipDiv.transition()                                    // declare the transition properties to bring fade-in div
                  .duration(50)                                  // it shall take 200ms
                  .style("opacity", .9);                          // and go all the way to an opacity of .9
                tooltipDiv.html('')  // add the text of the tooltip as html 
                  .style("left", (pageX) + "px")         // move it in the x direction 
                  .style("top", (pageY > 180 ? (pageY - 180) : 10) + "px")    // move it in the y direction
                  .style("background-image","url('slide_img/week" + lectureId + "_" + row.type + row.id + ".png')")
                  .style("background-size","contain")
                  .style("background-repeat","no-repeat");
              }
            }
          });
        })
        .on("mouseout", function() {
          tooltipDiv.transition()                                    // declare the transition properties to fade-out the div
            .duration(100)                                  // it shall take 500ms
            .style("opacity", 0);
        })
        .on("click", function(d) {
          var pageX = d3.mouse(this)[0];
          var pageY = d3.mouse(this)[1];
          var relTime = x.invert(d3.mouse(this)[0]).getTime();//normalized time in the video
          var slides, lectureId = d.name;
          d3.csv("slide_changes/" + lectureId + "-slide_changes.csv", function(data) {
            var endVideo = -1;
            //get length of video
            for(var i in data) {
              var row = data[i];
              var endTime = parseInt(row.end_time);
              if(endTime > endVideo) endVideo = endTime;
            }
            for(var i in data) {
              var row = data[i];
              var startTime = parseInt(row.start_time);
              var endTime = parseInt(row.end_time);
              if(startTime / endVideo * 100 < relTime &&
                  endTime / endVideo * 100 >= relTime) {
                $("#slide-dialog").html('<div class="slide-dialog" style="background:url(slide_img/week' + lectureId + '_' + row.type + row.id + '.png) no-repeat;background-size:contain;"></div>');
                $("#slide-dialog").dialog({
                  minWidth: 1000,
                  height: 600,
                  modal: true
                });
                // $("#slide-dialog").dialog("open");
              }
            }
          });
        });

    lecture.append("text")
        .datum(function(d) { return {name: d.name, value: d.values[d.values.length - 1]}; })
        .attr("transform", function(d) { return "translate(" + x(d.value.time) + "," + y(d.value.throughput) + ")"; })
        .attr("x", 3)
        .attr("dy", ".35em")
        .text(function(d) { return "Lecture " + d.name; });
}

function drawGostraight() {
  var lectures = [], percents = [],
      chart, x, y,
      width = 560,
      height,
      bar_height = 20;
  var gap = 5;

  var left_width = 200;

  for (var key in lectureDict) {
    lectures.push(key);
    percents.push(lectureDict[key].percent);
  }

  height = bar_height * lectures.length;

  x = d3.scale.linear()
     .domain([0, 100])
     .range([0, width]);

  // redefine y for adjusting the gap
  y = d3.scale.ordinal()
    .domain(percents)
    .rangeBands([0, (bar_height + 2 * gap) * percents.length]);

  chart = d3.select("#compare-dialog")
    .append('svg')
    .attr('class', 'gostraight_chart')
    .attr('width', left_width + width + 40)
    .attr('height', (bar_height + gap * 2) * percents.length + 30)
    .append("g")
    .attr("transform", "translate(10, 20)");
 
  chart.selectAll("line")
    .data(x.ticks(10))
    .enter().append("line")
    .attr("x1", function(d) { return x(d) + left_width; })
    .attr("x2", function(d) { return x(d) + left_width; })
    .attr("y1", 0)
    .attr("y2", (bar_height + gap * 2) * percents.length);
 
  chart.selectAll(".rule")
    .data(x.ticks(10))
    .enter().append("text")
    .attr("class", "rule")
    .attr("x", function(d) { return x(d) + left_width; })
    .attr("y", 0)
    .attr("dy", -6)
    .attr("text-anchor", "middle")
    .attr("font-size", 10)
    .text(String);
 
  chart.selectAll("rect")
    .data(percents)
    .enter().append("rect")
    .attr("x", left_width)
    .attr("y", function(d) { return y(d) + gap; })
    .attr("width", x)
    .attr("height", bar_height);
 
  chart.selectAll("text.score")
    .data(percents)
    .enter().append("text")
    .attr("x", function(d) { return x(d) + left_width; })
    .attr("y", function(d, i){ return y(d) + y.rangeBand()/2; } )
    .attr("dx", -5)
    .attr("dy", ".36em")
    .attr("text-anchor", "end")
    .attr('class', 'score')
    .text(function(d) { return d + '%'; });
 
  chart.selectAll("text.name")
    .data(lectures)
    .enter().append("text")
    .attr("x", left_width / 2)
    .attr("y", function(d, i){ return i * (bar_height + 2 * gap) + y.rangeBand()/2; } )
    .attr("dy", ".36em")
    .attr("text-anchor", "middle")
    .attr('class', 'name')
    .text(function(d) { return "Lecture " + d });
}