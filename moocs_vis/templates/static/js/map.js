var colorScale = ['#FFFFFF', '#FFEDA0', '#FEB24C', '#FD8D3C', '#FC4E2A', '#E31A1C', '#BD0026', '#800026'];
var valueScale = [10, 20, 50, 100, 200, 500, 1000];
var percentScale = [0, 0.5, 1, 2, 3, 5, 10];
var defaultColor = 'grey';
var option = 'seeks';
var map, geojson, info, options, highlighted, statenameVisible = false, year = 1980, month = 1;
// map = L.map('map').setView([22, 83], 4.7);
map = L.mapbox.map('map', 'examples.map-zgrqqx0w').setView([0, 0], 1);

// control zoom levels
map.on({
	// zoomend: resetSelectedState,
});

// cities markers
// citiesDataMod = citiesData
// citiesDataMod.features = citiesDataMod.features.slice(0, 20);
// citiesGeojson = L.geoJson(citiesDataMod, {
// 	// style: stateStyle,
// 	onEachFeature: onEachPoint,
// }).addTo(map);
// $(".leaflet-marker-pane").addClass("hidden");
// $(".leaflet-shadow-pane").addClass("hidden");

// control that shows state info on hover
info = L.control();

// var stats;
// $.ajax({
// 	dataType: "json",
// 	url: "/map/json/",
// 	async: false,
// 	success: function(data){ stats = data; }
// });

info.onAdd = function (map) {
	this._div = L.DomUtil.create('div', 'info');
	this.update();
	return this._div;
};

info.update = function (feature) {
	this._div.innerHTML = '<h4>' + option + '</h4>' +  (feature ?
		'<b>' + feature.properties.name + '</b><br />' + (getProp(feature.id) > 0 ? getProp(feature.id) : 0) + '% of learners making ' + option +
		'<br />Total learners: ' + (stats[feature.id] ? stats[feature.id].users : 'N/A')
		: 'Hover over a state');
};

info.addTo(map);

// add legend and initiate map
addLegendPercent(map);
drawMap();

// toggle of credits
var isCreditsVisible = true;
$('#toggle_credits').click(function(){
	$('#credits_box').slideToggle('fast');
	if(isCreditsVisible){
		$('#toggle_credits').html("Hide Information");
			isCreditsVisible = false;
		} else {
			$('#toggle_credits').html("Project Information");
			isCreditsVisible = true;
		}
});

// toggle of dashboard
var isDashboardVisible = true;
$('#toggle_dashboard').click(function(){
	$('#dashboard_box').slideToggle('fast');
	if(isDashboardVisible){
		$('#toggle_dashboard').html("Hide Dashboard");
			isDashboardVisible = false;
		} else {
			$('#toggle_dashboard').html("Dashboard");
			isDashboardVisible = true;
		}
});

$("#option").on("change", function() {
	option = $(this).val();
	drawMap();
});

// slider controller

// $( "#slider_year" ).labeledslider({
// 	value: year,
// 	min: 1980,
// 	max: 1990,
// 	step: 10,
// 	slide: function( event, ui ) {
// 		year = ui.value;
// 		drawMap();
// 	}
// });

// $( "#slider_month" ).labeledslider({
// 	value: year,
// 	min: 1,
// 	max: 12,
// 	step: 1,
// 	tickLabels: {
//       1:'Jan',
//       2:'Feb',
//       3:'Mar',
//       4:'Apr',
//       5:'May',
//       6:'Jun',
//       7:'Jul',
//       8:'Aug',
//       9:'Sep',
//       10:'Oct',
//       11:'Nov',
//       12:'Dec',
//     },
// 	slide: function( event, ui ) {
// 		month = ui.value;
// 		drawMap();
// 	}
// });

// $("#state_info_btn").on("click", function() {
// 	$("#chart_dialog").html('');
// 	$("#chart_dialog").append($("<iframe id='chart_iframe' />").attr("src", "stackedchart.html"));
// 	$("#chart_dialog").dialog({
// 		width: $(window).width(),
// 		height: $(window).height(),
// 		title: "Stacked Chart",
// 		modal: true,
//     });
// });

function drawMap() {
	highlighted = null;
	if(geojson) {
		map.removeLayer(geojson);
	}
	geojson = L.geoJson(countries, {
		style: stateStyle,
		onEachFeature: onEachFeature,
	}).addTo(map);

	// $.each(citiesData, function(i, city) {
 //    	geojson.addData(city);
 //    	if(i > 30) {
 //    		return false;
 //    	}
 //  	});
	// geojson.addData({
 //        type: 'Point',
 //        id: "New Delhi",
 //        coordinates: [Math.random() * 360 - 180, Math.random() * 160 - 80],
 //    });
}

// get color depending on population density value
function getColor(d) {
	if(d == -1) return defaultColor;
	if(d == 0) return colorScale[0];
	for(i = percentScale.length; i >= 0; i--) {
		if(d > percentScale[i]) {
			return colorScale[i + 1];
		}
	}
	return defaultColor;
}

function stateStyle(feature) {
	return {
		weight: 1,
		color: 'grey',
		dashArray: '4',
		fillOpacity: 0.6,
		fillColor: getColor(getProp(feature.id))
	};
}

function getProp(id) {
	if(stats[id]) {
		if(stats[id].users == 0) return -1;
		return stats[id][option];
	} else {
		return -1;
	}
}

function highlightFeature(e) {
	var layer = e.target;

	if (layer && highlighted !== layer) {
		layer.setStyle({
			weight: 3,
			color: 'green',
			dashArray: '',
			fillOpacity: 0.6
		});
	}
	info.update(layer.feature);
}

function resetHighlight(e) {
	geojson.resetStyle(e.target);
	info.update();
}

function zoomToFeature(e) {
	var layer = e.target;
	if (layer && highlighted !== layer) {
		map.fitBounds(e.target.getBounds());
		// if(!statenameVisible) {
		// 	$("#state_info").slideToggle('fast');
		// 	statenameVisible = true;
		// }
		highlighted = layer;
		// $("#state_name").html(layer.feature.id);
		// $("#state_info_btn").attr('data-state', layer.feature.id);
		// $("#state_info").removeClass("hidden");
		// prev = highlighted;
		// resetHighlight(prev._container);
		// layer.setStyle({
		// 	weight: 3,
		// 	color: 'black',
		// 	dashArray: '',
		// 	fillOpacity: .4
		// });
	} else {
		map.setView([0, 0], 1);
		highlighted = null;
		// $("#state_info").slideToggle('fast');
		// statenameVisible = false;
		// $("#state_info").addClass("hidden");
		// e.target.setStyle({
		// 	fillOpacity: 0.7
		// });
	}
}

function resetSelectedState(e) {
	if(map.getZoom() < 6 && highlighted) {
		highlighted = null;
		// $("#state_info").slideToggle('fast');
		// statenameVisible = false;
	}
	// if(map.getZoom() < 7) {
	// 	$(".leaflet-marker-pane").addClass("hidden");
	// 	$(".leaflet-shadow-pane").addClass("hidden");
	// } else {
	// 	$(".leaflet-marker-pane").removeClass("hidden");
	// 	$(".leaflet-shadow-pane").removeClass("hidden");
	// }
}

function onEachFeature(feature, layer) {
	layer.on({
		mouseover: highlightFeature,
		mouseout: resetHighlight,
		click: zoomToFeature,
	});
}

function onEachPoint(feature, layer) {
	layer.on({
		mouseover: highlightPoint,
		mouseout: resetPoint,
		click: detailToPoint,
	});
}

function highlightPoint(e) {
	info.update(e.target.feature);
}

function resetPoint(e) {
	info.update();
}

function detailToPoint(e) {
	$("#chart_dialog").html('');
	$("#chart_dialog").append($("<iframe id='chart_iframe' />").attr("src", "timeseries.html"));
	$("#chart_dialog").dialog({
		width: $(window).width(),
		height: $(window).height(),
		title: "Time Series Chart",
		modal: true,
    });
}

function addLegendPercent(map) {
	var legend = L.control({position: 'bottomright'});

	legend.onAdd = function (map) {

		var div = L.DomUtil.create('div', 'info legend'),
			labels = [],
			from, to;

		labels.push("Percent (%)");
		labels.push(
				'<i style="background:' + defaultColor + '"></i> No learner');

		labels.push(
				'<i style="background:' + getColor(0) + '"></i> 0');

		for (var i = 0; i < percentScale.length; i++) {
			from = percentScale[i];
			to = percentScale[i + 1];

			labels.push(
				'<i style="background:' + getColor(from + 0.1) + '"></i> ' +
				from + (to ? '&ndash;' + to : '+'));
		}

		div.innerHTML = labels.join('<br>');
		return div;
	};

	legend.addTo(map);
}

// function addLegend(map) {
// 	var legend = L.control({position: 'bottomright'});

// 	legend.onAdd = function (map) {

// 		var div = L.DomUtil.create('div', 'info legend'),
// 			labels = [],
// 			from, to;

// 		for (var i = 0; i < valueScale.length; i++) {
// 			from = valueScale[i] * 100000;
// 			to = valueScale[i + 1] * 100000;

// 			labels.push(
// 				'<i style="background:' + getColor(from + 1) + '"></i> ' +
// 				from + (to ? '&ndash;' + to : '+'));
// 		}

// 		div.innerHTML = labels.join('<br>');
// 		return div;
// 	};

// 	legend.addTo(map);
// }
