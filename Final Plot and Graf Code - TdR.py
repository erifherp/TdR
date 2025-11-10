import csv
import glob
import xml.etree.ElementTree as ET
import matplotlib.pyplot as plt
import math
import numpy as np
from mpl_toolkits.mplot3d import Axes3D

################################################################
# Variable definitions
################################################################

# A dictionary to store the tonal functions read from the .csv
# The key is the position (in eighth notes) and the value is the
# tonal function.
tonal_functions = {}

# A dictionary to store the nodes, each node being a combination
# of a note and a tonal function. The key takes the form
# "note-tonal_function", and the value # is the count of
# appearances of the combination.
nodes_dictionary = {}

# A dictionary to store the edges between nodes. The key is the
# combination of two nodes in the form "node1|node2", and the
# value is the weight of the edge.
edges_dictionary = {}

################################################################
# Function to load the tonal functions from a CSV file
################################################################
def load_tonal_functions(csv_file_name):
  with open(csv_file_name, mode='r') as csv_file:
    csv_reader = csv.reader(csv_file)
    for row in csv_reader:
      position = row[1]
      function = row[2]
      tonal_functions[position] = function

################################################################
# Function to load the nodes dictionary from a MusicXML file
################################################################
def load_nodes_dictionary(xml_file_name):

  # Load and parse the MusicXML file
  tree = ET.parse(xml_file_name)
  root = tree.getroot()

  # To track the accumulated duration in sixteenth notes
  accumulated_position_sixteenths = 0

  # To track the current measure number
  measure_no = 0

  # Iterate through each measure and note
  for measure in root.findall('.//measure'):
    current_voice = None
    for note in measure.findall('.//note'):

      # Check for voice changes
      new_voice = note.find('voice').text
      if new_voice != current_voice:
        accumulated_position_sixteenths = measure_no * 16
      current_voice = new_voice

      # Find the position of the note within the measure
      position_sixteenths = (
        (accumulated_position_sixteenths - 1) // 2) + 1
      duration_sixteenths = note.find('duration')
      accumulated_position_sixteenths += int(
        duration_sixteenths.text)

      # If the note is not a rest, find the pitch
      pitch = note.find('pitch')
      if pitch is not None:
        step = pitch.find('step').text

        # Build the node key and update the count
        tonal_function = tonal_functions.get(
          str(position_sixteenths))
        if tonal_function is not None:
          key = f"{step}-{tonal_function}"
          nodes_dictionary[key] = nodes_dictionary.get(
            key, 0) + 1
    
    # Move to the next measure and go to next iteration
    measure_no += 1

################################################################
# Function to calculate an edge weight between two notes
################################################################
def calculate_edge_weight(position1, position2, voice1, voice2):
  distance = position1 - position2
  if distance <= 5 and position2 <= position1:
    if voice1 == voice2:
      if distance == 1:
        return 8
      elif distance == 2:
        return 5
      elif distance == 3:
        return 3
      elif distance == 4:
        return 2
      elif distance == 5:
        return 1
      else:
        return 0
    else:
      if position1 == position2:
        return 10
      elif distance == 1:
        return 7
      elif distance == 2:
        return 4
      elif distance == 3:
        return 2
      elif distance == 4:
        return 1
      else:
        return 0
  return 0

################################################################
# Function to load the edges dictionary from a MusicXML file
################################################################
def load_edges_dictionary(xml_file_name):

  # Load and parse the MusicXML file
  tree = ET.parse(xml_file_name)
  root = tree.getroot()

  # To track the last measure processed
  last_measure = None

  # To track the accumulated durations in sixteenth notes
  accumulated_position1_sixteenths = 0
  accumulated_position2_sixteenths = 0
  
  # To track the current measure number
  measure_no = 0

  # Iterate through each measure and note
  for measure in root.findall('.//measure'):
    current_voice1 = None
    for note1 in measure.findall('.//note'):

      # Check for voice changes
      new_voice1 = note1.find('voice').text
      if new_voice1 != current_voice1:
        accumulated_position1_sixteenths = measure_no * 16
      current_voice1 = new_voice1

       # Find the position of the note within the measure
      position1_sixteenths = (
        (accumulated_position1_sixteenths - 1) // 2) + 1
      duration1_sixteenths = note1.find('duration')
      accumulated_position1_sixteenths += int(
        duration1_sixteenths.text)

      # Only consider non-rest notes
      if note1.find('rest') is None:

        # Process notes from the last measure
        if last_measure is not None:
          current_voice2 = None
          for note2 in last_measure.findall('.//note'):

            # Check for voice changes
            new_voice2 = note2.find('voice').text
            if new_voice2 != current_voice2:
              accumulated_position2_sixteenths = (
              measure_no - 1) * 16
            current_voice2 = new_voice2

            # Find the position of the note within
            # the measure
            position2_sixteenths = (
              (accumulated_position2_sixteenths
               - 1) // 2) + 1
            duration2_sixteenths = note2.find(
              'duration')
            accumulated_position2_sixteenths += int(
              duration2_sixteenths.text)

            # Calculate the edge weight
            edge_weight = calculate_edge_weight(
              position1_sixteenths,
              position2_sixteenths,
              new_voice1, new_voice2)

            # Only consider non-rest notes
            # and non-zero edge weights
            if note2.find('rest') is None and edge_weight != 0:

              pitch1 = note1.find('pitch')
              pitch2 = note2.find('pitch')
              if pitch1 is not None and pitch2 is not None:
                step1 = pitch1.find('step').text
                step2 = pitch2.find('step').text
                tonal_function1 = tonal_functions[
                  str(position1_sixteenths)]
                tonal_function2 = tonal_functions[
                  str(position2_sixteenths)]
                subkey1 = step1 + '-' + tonal_function1
                subkey2 = step2 + '-' + tonal_function2
                key = f"{subkey1}|{subkey2}"
                edges_dictionary[key] = edges_dictionary.get(
                  key, 0) + edge_weight

        current_voice2 = None
        for note2 in measure.findall('.//note'):

          # Check for voice changes
          new_voice2 = note2.find('voice').text
          if new_voice2 != current_voice2:
            accumulated_position2_sixteenths = measure_no * 16
          current_voice2 = new_voice2

          # Find the position of the note within
          # the measure
          position2_sixteenths = (
            (accumulated_position2_sixteenths
             - 1) // 2) + 1
          duration2_sixteenths = note2.find(
            'duration')
          accumulated_position2_sixteenths += int(
            duration2_sixteenths.text)

          # Calculate the edge weight
          edge_weight = calculate_edge_weight(
            position1_sixteenths,
            position2_sixteenths,
            new_voice1, new_voice2)

          # Only consider non-rest notes
          # and non-zero edge weights
          if note2.find('rest') is None and edge_weight != 0:
            pitch1 = note1.find('pitch')
            pitch2 = note2.find('pitch')
            if pitch1 is not None and pitch2 is not None:
              step1 = pitch1.find('step').text
              step2 = pitch2.find('step').text
              tonal_function1 = tonal_functions[
                str(position1_sixteenths)]
              tonal_function2 = tonal_functions[
                str(position2_sixteenths)]
              subkey1 = step1 + '-' + tonal_function1
              subkey2 = step2 + '-' + tonal_function2
              key = f"{subkey1}|{subkey2}"
              edges_dictionary[key] = edges_dictionary.get(
                key, 0) + edge_weight
    
    for edge in list(edges_dictionary.keys()):
      if edges_dictionary[edge] < 5:
        del edges_dictionary[edge]
    last_measure = measure
    measure_no += 1

################################################################
# Function to calculate the entropy
################################################################
def calculate_entropies():
  edges_value = 1.0
  nodes_value = 0.1
  entropies = {}
  min_entropy = 5

  for node in nodes_dictionary:
    sum_edges = 0
    sum_nodes = 0
    for edge in edges_dictionary:
      first_node, second_node = edge.split('|')
      if node == first_node:
        sum_edges += edges_dictionary[edge]
        sum_nodes += nodes_dictionary[second_node]
      
    for edge in edges_dictionary:
      first_node, second_node = edge.split('|')
      if node == first_node:
        print(edges_dictionary[edge], sum_edges,
           nodes_dictionary[second_node], sum_nodes)


        S_aresta = (
          edges_dictionary[edge] / sum_edges) * edges_value + (
          nodes_dictionary[second_node] / sum_nodes) * nodes_value
        entropia_aresta = round(S_aresta * 100, 2)
        
        # Filter entropies less or equal to 5
        if entropia_aresta > min_entropy:
          entropies[edge] = entropia_aresta
  
  return entropies

################################################################
# Main program - Load files
################################################################

# Find the first .csv and .musicxml files in the current folder
csv_file_name = glob.glob('*.csv')[0] if glob.glob(
  '*.csv') else None
xml_file_name = glob.glob('*.musicxml')[0] if glob.glob(
  '*.musicxml') else None

# Load the tonal functions, nodes, and edges
load_tonal_functions(csv_file_name)
print(tonal_functions)

load_nodes_dictionary(xml_file_name)
print(nodes_dictionary)
print(f"Node count: {len(nodes_dictionary)}")

load_edges_dictionary(xml_file_name)
print(edges_dictionary)
print(f"Edge count: {len(edges_dictionary)}")

################################################################
# Main program - Nodes graph visualization
################################################################

# Create 'figure' and 'axes' for matplotlib
fig, ax = plt.subplots(figsize=(14, 14))
    
# Calculate the nodes position in a circle
positions = {}
nodes = list(nodes_dictionary.keys())
center_x, center_y, radius = 0, 0, 1.5
angle_per_node = 2 * math.pi / len(nodes)

for i, node in enumerate(nodes):
  angle = i * angle_per_node
  x = center_x + radius * math.cos(angle)
  y = center_y + radius * math.sin(angle)
  positions[node] = (x, y)

# Draw the edges (the connecting lines)
for edge, weight in edges_dictionary.items():
  try:
    source, target = edge.split('|')
    if source in positions and target in positions:
      source_x, source_y = positions[source]
      target_x, target_y = positions[target]

      # Set the line width based on the weight
      width = max(0.5, math.log(weight) / 2)

      # Margin to avoid arrows overlapping with nodes
      margin = 15

      # Draw the arrow from source to target
      ax.annotate("",
        xy=(target_x, target_y), 
        xytext=(source_x, source_y),
        arrowprops=dict(
          arrowstyle="->", 
          color="gray", 
          linewidth=width,
          shrinkA=margin,
          shrinkB=margin,
          patchA=None,
          patchB=None,
          connectionstyle="arc3,rad=0.1",
        ))
  except ValueError:
    print(f"Error while processing edge: {edge}")

# Draw arrows for edges with significant weights in red
for edge, weight in edges_dictionary.items():
  try:
    source, target = edge.split('|')
    if source in positions and target in positions:
      source_x, source_y = positions[source]
      target_x, target_y = positions[target]

      # Filter for significant weights
      if math.log(weight) / 2 >= 2:

        # Set the line width based on the weight
        width = max(0.5, math.log(weight) / 2)

        # Margin to avoid arrows overlapping with nodes
        margin = 15

        # Dibuixem una fletxa de l'origen al destí
        ax.annotate("",
          xy=(target_x, target_y), 
          xytext=(source_x, source_y),
          arrowprops=dict(
            arrowstyle="->", 
            linewidth=width,
            color="red", 
            shrinkA=margin,
            shrinkB=margin,
            patchA=None,
            patchB=None,
            connectionstyle="arc3,rad=0.1",
          ))
  except ValueError:
    print(f"Error while processing edge: {edge}")

# Draw the nodes and their labels
for node, pos in positions.items():
  x, y = pos

  # Determine the size of the node based on its frequency
  size = nodes_dictionary.get(node, 1) * 35
  
  # Draw the node as a scatter point
  # Using z-order = 5 to ensure nodes are on top of edges
  ax.scatter(x, y, s=size, color='skyblue', zorder=5)
  
  # Draw the node label
  ax.text(x, y, node, ha='center', va='center',
    fontsize=9, zorder=10)

# Final adjustments and display
ax.set_title("Graf de les relacions entre Funcions Tonals",
    fontsize=16)
ax.set_aspect('equal', adjustable='box') # Ensure circle shape
plt.axis('off') # Hide axis
plt.tight_layout()
plt.show()

################################################################
# Main program - Plot visualization
################################################################

# Calculate entropies
entropies_dictionary = calculate_entropies()
print(entropies_dictionary)

# Create a numeric map for EACH unique node
all_nodes = list(nodes_dictionary.keys())
node_map = {node: i for i, node in enumerate(all_nodes)}
print("\nMapping nodes to coordinates:")
print(node_map)

x_data = [] # Source node
y_data = [] # Target node
z_data = [] # Entropy value

nodes_x = []
nodes_y = []

for edge, entropy in entropies_dictionary.items():
  if entropy > 5:
    source, desti = edge.split('|')

    # Check that both source and target are in our map
    if source in node_map and target in node_map:
      # X axis -> Number of the source node
      x_data.append(node_map[source])
      nodes_x.append(source)

      # Y axis -> Number of the target node
      y_data.append(node_map[desti])
      nodes_y.append(desti)

      # Z axis -> Entropy value
      z_data.append(entropy)

# Convert to numpy arrays for matplotlib
x = np.array(x_data)
y = np.array(y_data)
z = np.array(z_data)

# Create 3D figure
fig = plt.figure(figsize=(12,8))
ax = fig.add_subplot(111, projection='3d')

surf = ax.plot_trisurf(x, y, z, cmap='viridis', shade=True,
  antialiased=True)

ax.set_xlabel('Node Origen', labelpad=35)
ax.set_ylabel('Node Destí', labelpad=35)
ax.set_zlabel('Entropia Calculada (%)')

# Set labels for axis X and Y to show ONLY the real nodes
ax.set_xticks(list(node_map.values()))
x_labels = ax.set_xticklabels([f"{node}------------" 
  if i % 2 == 0 else node for i, node in enumerate(
    node_map.keys())], rotation=45, ha='right', fontsize=7)

ax.set_yticks(list(node_map.values()))
y_labels = ax.set_yticklabels([f"------------{node}"
  if i % 2 == 0 else node for i, node in enumerate(
    node_map.keys())], rotation=-15, ha='left', fontsize=7)

fig.colorbar(surf, ax=ax, shrink=0.6, aspect=10,
  label='Entropia (%)')
ax.legend()

# Adjust the layout so that labels do not overlap
plt.tight_layout()

# Show the plot
plt.show()
