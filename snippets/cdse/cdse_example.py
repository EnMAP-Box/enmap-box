import time

import openeo

con = openeo.connect("https://openeo.dataspace.copernicus.eu").authenticate_oidc()

lon, lat = 13.42, 52.47

bands = ["B01", "B02", "B03", "B04", "B05", "B06", "B07", "B08", "B8A", "B09", "B11", "B12"]

cube = con.load_collection(
    "SENTINEL2_L2A",
    spatial_extent={"west": lon, "east": lon, "south": lat, "north": lat},
    temporal_extent=["2024-05-17", "2024-05-17"],
    bands=bands
)

feature = {
    "type": "Point",
    "coordinates": [lon, lat]
}

result = cube.aggregate_spatial(
    geometries=feature,
    reducer="mean"

)

t0 = time.time()
values = result.execute()
print(values)
print(time.time() - t0)
