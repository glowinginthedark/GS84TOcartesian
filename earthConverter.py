import math

EARTH_RADIUS = 6371

def WGS84_to_cartesian(latitude, longitude, altitude):
	coordinates = [distance_x(latitude, longitude, altitude),distance_y(latitude, longitude, altitude), distance_z(latitude, altitude)]
	return coordinates

def distance_x(latitude, longitude, altitude):
	return (EARTH_RADIUS + altitude) * math.cos(math.radians(latitude)) * math.cos(math.radians(longitude))

def distance_y(latitude, longitude, altitude):
	return (EARTH_RADIUS + altitude) * math.cos(math.radians(latitude)) * math.sin(math.radians(longitude))

def distance_z(latitude, altitude):
	return (EARTH_RADIUS + altitude) * math.sin(math.radians(latitude))	