import os
import sys
import csv
import earthConverter
import matplotlib as mpl
from mpl_toolkits.mplot3d import Axes3D
import numpy as np
import matplotlib.pyplot as plt

MAX_FILES = 10
options = []

def scan_and_get_csv_paths(pdir):
	ext_check = '.csv'
	list_f = []

	if os.path.isdir(pdir):
		for root, pd, fs in os.walk(pdir):
			for f in fs:
				if f[-1*len(ext_check):] == ext_check and len(list_f) < 10:
					list_f.append(os.path.join(root, f))

		if len(list_f) == 0:
			print("there are no", ext_check, "files in the folder provided. exiting...")
			sys.exit()

		return list_f
	else:
		return False

def locate_csv_columns(filename):
	file = None
	keywords = ('latitude', 'longitude', 'altitude')

	col_longitude = 0
	col_latitude = 0
	col_altitude = 0

	file = open(filename)

	with file as csv_file:
		csv_reader = csv.reader(csv_file, delimiter=',')
		line_count = 0

		for row in csv_reader:

			if line_count == 0:

				for z in keywords:
					
					for a in range(len(row)):
						if row[a].find(z) != -1:
							if z == 'latitude':
								col_latitude = a
							elif z == 'longitude':
								col_longitude = a
							else:
								col_altitude = a

				line_count += 1
			else:
				return [col_latitude, col_longitude, col_altitude]

def get_xyz_coordinates(file, columns):
	xyz = []

	with file as csv_file:
		csv_reader = csv.reader(csv_file, delimiter=',')
		line_count = 0

		for row in csv_reader:
			if line_count == 0:
				line_count += 1
				continue
			else:
				latitude = float(row[columns[0]])
				longitude = float(row[columns[1]])
				altitude = float(row[columns[2]])
				xyz = xyz + [(earthConverter.WGS84_to_cartesian(latitude, longitude, altitude))]
				#xyz = xyz + [[latitude, longitude, 3, 3]]
				line_count += 1


	return xyz

def trajectory_new_origin(xyz, origin):
	xyz_new_origin = []

	for p in range(len(xyz)):
		xyz_new_origin.append([])
		for d in range(3):
			xyz_new_origin[p].append(xyz[p][d] - origin[d])

	return xyz_new_origin

def coordinates_by_axis(xyz):
	d_lists = []

	for i in range(3):
		d_lists.append([])
		for point in xyz:
				d_lists[i].append(point[i])

	return d_lists

def make_trajectory_components_positive(n_xyz, origin=None):
	d_lists = coordinates_by_axis(n_xyz)
	if origin is None:
		origin = [d_lists[0][0], d_lists[1][0], d_lists[2][0]]
	return trajectory_new_origin(n_xyz, origin)

def process_csv(file_f, normalize=True):
	columns = locate_csv_columns(file_f)
	file = open(file_f)
	xyz = get_xyz_coordinates(file, columns)
	
	if normalize:
		xyz = make_trajectory_components_positive(xyz)

	return xyz

def plot_coordinates(plots):
	if '-s' in options and len(plots) > 1:
		for plot in plots:
			plot_coordinates([plot])
			
		return

	mpl.rcParams['legend.fontsize'] = 10
	fig = plt.figure()
	ax = fig.gca(projection='3d')

	for plot in plots:
		cba = coordinates_by_axis(plot[0])

		for d in range(len(cba)):
			cba[d] = [k*100 for k in cba[d]]

		ax.plot(cba[0], cba[1], cba[2], label=plot[1])

	ax.legend()
	plt.show()

def create_dir(dir):
	if not os.path.exists(dir): # if the directory does not exist
	    os.makedirs(dir) # make the directory
	else: # the directory exists
	    #removes all files in a folder
	    for the_file in os.listdir(dir):
	        file_path = os.path.join(dir, the_file)
	        try:
	            if os.path.isfile(file_path):
	                os.unlink(file_path) # unlink (delete) the file
	        except Exception as e:
	            print(e)

def write_converted_coordinates(destination_folder, plots):
	c = 0
	for plot in plots:
		c+=1
		fname = os.path.join(destination_folder, 'cartesian_' + str(c) + '.csv')

		with open(fname, mode='w+') as csv_file:
			writer = csv.writer(csv_file, delimiter=',',
                            quotechar='|', quoting=csv.QUOTE_MINIMAL, lineterminator = '\n')
			writer.writerow(['x', 'y', 'z'])
			xyz = plot[0]
			for x in range(len(xyz)):
				writer.writerow([xyz[x][0], xyz[x][1], xyz[x][2]])

def make_entire_graph_positive(plots):
	d_lists = []

	for plot in plots:
		d_lists += [coordinates_by_axis(plot[0])]

	mins = [0, 0, 0]

	for dlist in d_lists:
		for d in range(len(dlist)):
			if min(dlist[d]) < mins[d]:
				mins[d] = min(dlist[d])

	for dlist in d_lists:
		for d in range(len(dlist)):
			for proj_d in dlist[d]:
				proj_d += mins[d]

	for plot in plots:
		plot[0] = trajectory_new_origin(plot[0], mins)

	return plots

def setup_and_validate_input():
	paths = None
	files= []
	destination_folder = None
	current_dir = os.getcwd()
	fileargs = []

	#get {a list of files OR directory containing .csv files} and/or a {destination_folder} all from one stdin/sys.argv
	if len(sys.argv) > 1:
		for arg in sys.argv:
			if arg[0] == '-':
				options.append(arg)
			else:
				fileargs.append(arg)

		paths = fileargs[1:MAX_FILES - 1]		
	else:
		inp = input("path to folder | paths to csv files (you can also provide it as a command line argument):\n")
		paths = inp.split(' ')[:MAX_FILES - 1]

	#check if a direcotry is provided and use it
	potential_dir = os.path.join(current_dir, paths[0])
	dircheck = scan_and_get_csv_paths(potential_dir)

	if dircheck != False:
		#if potential_dir exists, get the returned list of csv files from that folder
		files = dircheck
	else:
		ext_check = '.csv'

		for f in paths:
			if os.path.isdir(f):
				continue
			elif f[-1*len(ext_check):] == ext_check and len(files) < 10:
				files.append(f)

	#check if destination_folder is provided in the input (sys.argv/stdin) and use it, otherwise create one
	if ( os.path.isdir(paths[-1]) or os.path.isdir(os.path.join(current_dir, paths[-1])) ) and paths[-1] != paths[0]:
		destination_folder = paths[-1]
	else:
		destination_folder = os.path.join(current_dir, "cartesian")
		create_dir(destination_folder)

	return files, destination_folder

print('\n')
print('                         Earth Converter                     ')
print('-------------------------------------------------------------')
print("This tool reads csv files containing GPS coordinates, and makes")
print("use of:-")
print("    - earthConverter.py")
print("    - numpy")
print("    - matplotlib")
print("    - the csv module")
print("to convert and plot the coordinates to cartesian as well print")
print("them to a new csv file")
print('-------------------------------------------------------------')
print('\n')
print('USAGE: python convertCoordinates.py [path_to_csv_file1] [file2] ... [file' + str(MAX_FILES) + '] [destination_folder]')
print('USAGE: python convertCoordinates.py [path_to_folder] [destination_folder]')
print("if no destination_folder is specified, one called 'cartesian'")
print("will be created.") 
print('-------------------------------------------------------------')
print("options:-")
print(" -n do not normalize converted coordinates to a common start point")
print(" -s plot all graphs separately")
print('-------------------------------------------------------------')
print('\n')
print("Your csv file:-")
print(" - must have columns that start at the top of the spreadsheet")
print(" - must have at least 3 columns of data storing altitude,")
print("   longitude, and latitude values (your first row should")
print("   contain the words 'altitude', 'longitude', and 'latitude')")
print(" - must contain the data in the first sheet of the workbook")
print('\n')
print("note: a maximum of " + str(MAX_FILES) + " files can be processed per run.")
print('-------------------------------------------------------------')

files, destination_folder = setup_and_validate_input()

#process .csv files, convert coordinates, and produce plot data
plots = []
for file in files:
	coordinates = None

	if '-n' in options:
		coordinates = process_csv(file, False)
	else:
		coordinates = process_csv(file)

	plots  = plots + [[coordinates, file]]

make_entire_graph_positive(plots)

print('plotting data...')
plot_coordinates(plots)

print('saving plot data to new files...')
write_converted_coordinates(destination_folder, plots)