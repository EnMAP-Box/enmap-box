<div id="info">foobar</div>
[% array_to_string(from_json(raster_profile(@layer_name, geometry:=@layer_cursor_point))['y']) %]

[% raster_profile(@layer_name, geometry:=@layer_cursor_point) %]

<script>
var profile = [% from_json(raster_profile(@layer_name, geometry:=@layer_cursor_point)) %]

// var myPlot = document.getElementById('graphDiv');
myInfo = document.getElementById('info');
myInfo.innerHTML = profile

</script>




## Example: QgsMapTip with Spectral Profile Plot

<h3>Pixel Profile</h3>
Location: [% x(@layer_cursor_point) %], [% y(@layer_cursor_point) %] <br>
CRS: [%@layer_crs%]

<div style="min-with:200px;" id="graphDiv"></div>
<script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
<script>
var profile = JSON.parse(' [% raster_profile(@layer_name, geometry:=@layer_cursor_point) %] ');

var data = [{x:profile['x'].filter, 
		     y:profile['y'],
			 type:'scatter'
			}];
			
var layout = {
  autosize: false,
  paper_bgcolor: 'white',
  plot_bgcolor: 'white',
};
Plotly.react(graphDiv, data, layout);
</script>

