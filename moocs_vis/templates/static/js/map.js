var colorScale = ['#FFFFFF', '#FFEDA0', '#FEB24C', '#FD8D3C', '#FC4E2A', '#E31A1C', '#BD0026', '#800026'];
var valueScale = [10, 20, 50, 100, 200, 500, 1000];
var percentScale = {
	// 'event-based' : [0, 10, 20, 30, 40, 50, 60], // for all except ratechange
	'event-based' : [0, 1, 2, 3, 4, 5, 10],
	// 'userbased' : [0, 0.5, 1, 2, 3, 5, 10],
	'user-based' : [0, 20, 30, 35, 40, 50, 60],
};
var defaultColor = 'grey';
var behavior_option = 'uprate';
var method_option = 'event-based';
var lecture = 'all';
var map, geojson, info, options, highlighted, statenameVisible = false, year = 1980, month = 1;
map = L.mapbox.map('map', 'examples.map-zgrqqx0w').setView([30, 0], 2);

// control that shows state info on hover
info = L.control();

info.onAdd = function (map) {
	this._div = L.DomUtil.create('div', 'info');
	this.update();
	return this._div;
};

info.update = function (feature) {
	var measure = ' events/user, events = '
	if(method_option == 'user-based') {
		measure = ' % of learners making ';
	}
	this._div.innerHTML = '<h4>' + method_option + ' ' + behavior_option + '</h4>' +  (feature ?
		'<b>' + feature.properties.name + '</b><br />' +
		(getProp(feature.id) > 0 ? getProp(feature.id) : 0) + measure + behavior_option +
		'<br>num_' + behavior_option + ': ' + (stats[lecture][method_option][feature.id] ? stats[lecture][method_option][feature.id]['num_' + behavior_option] : 'N/A') +
		'<br />Total learners: ' + (stats[lecture][method_option][feature.id] ? stats[lecture][method_option][feature.id].users : 'N/A')
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

$("#lecture_option").on("change", function() {
	lecture = $(this).val();
	updateOptions();
	drawMap();
});

$("#behavior_option").on("change", function() {
	updateOptions();
	drawMap();
});

$("#method_option").on("change", function() {
	updateOptions();
	addLegendPercent(map);
	drawMap();
});

function updateOptions() {
	method_option = $("#method_option").val();
	behavior_option = $("#behavior_option").val();
}

function drawMap() {
	highlighted = null;
	if(geojson) {
		map.removeLayer(geojson);
	}
	geojson = L.geoJson(countries, {
		style: stateStyle,
		onEachFeature: onEachFeature,
	}).addTo(map);
}

function getColor(d) {
	if(d == -1) return defaultColor;
	if(d == 0) return colorScale[0];
	for(i = percentScale[method_option].length; i >= 0; i--) {
		if(d > percentScale[method_option][i]) {
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
	if(stats[lecture][method_option][id]) {
		if(stats[lecture][method_option][id].users == 0) return -1;
		return stats[lecture][method_option][id][behavior_option];
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
		highlighted = layer;
	} else {
		map.setView([30, 0], 2);
		highlighted = null;
	}
}

function resetSelectedState(e) {
	if(map.getZoom() < 6 && highlighted) {
		highlighted = null;
	}
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
	$(".info.legend").remove();
	var legend = L.control({position: 'bottomright'});

	legend.onAdd = function (map) {

		var div = L.DomUtil.create('div', 'info legend'),
			labels = [],
			from, to;
		labels.push(method_option == "user-based" ? "Behaving users (%)" : "Events/user");
		labels.push(
				'<i style="background:' + defaultColor + '"></i> No learner');

		labels.push(
				'<i style="background:' + getColor(0) + '"></i> 0');

		for (var i = 0; i < percentScale[method_option].length; i++) {
			from = percentScale[method_option][i];
			to = percentScale[method_option][i + 1];

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
