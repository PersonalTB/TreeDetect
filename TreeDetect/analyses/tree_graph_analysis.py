import pandas as pd
from TreeDetect.data_preparation.preprocess import (create_delaunay_graph_from_geographic_points)

def graph_analysis(csv_filepath, settings):
	points = pd.read_csv(csv_filepath)
	lon_lat_coords = points[['longitude','latitude']].to_numpy()
