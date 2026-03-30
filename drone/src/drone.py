import geopandas as gpd
import matplotlib.pyplot as plt
import networkx as nx
from shapely.geometry import LineString, Point
import numpy as np
import json
from math import dist
import matplotlib.animation as animation
import os

def generate_drone_output(geojson_path: str, output_path: str, result_path: str):
    gdf = gpd.read_file(geojson_path)
    
    gdf = gdf[gdf.geometry.type == 'LineString']

    G = nx.Graph()

    for idx, row in gdf.iterrows():
        line: LineString = row.geometry
        coords = np.array(line.coords)
        if len(coords) < 2:
            continue
        start = tuple(coords[0])
        end = tuple(coords[-1])
        name = row.get("ODONYME") or row.get("NOM_VOIE") or "Rue inconnue"
        length = np.sum(np.linalg.norm(coords[1:] - coords[:-1], axis=1)) * 111000
        G.add_edge(start, end, geometry=line, name=name.strip(), length=round(length, 1))

    if not nx.is_connected(G):
        largest_cc = max(nx.connected_components(G), key=len)
        G = G.subgraph(largest_cc).copy()

    from networkx.algorithms.euler import eulerize, eulerian_circuit
    if not nx.is_eulerian(G):
        G = eulerize(G)

    circuit = list(eulerian_circuit(G))

    path_lines = []
    segment_lengths = []
    total_distance = 0.0
    for u, v in circuit:
        data = G.get_edge_data(u, v)

        if data is None or "length" not in data:
            length = dist(u, v) * 111000
            total_distance += length
            path_lines.append(LineString([u, v]))
            segment_lengths.append(length)
        else:
            total_distance += data["length"]
            path_lines.append(data["geometry"])
            segment_lengths.append(data["length"])
    

            
    sampling_factor = 1

    all_coords = np.concatenate([np.array(line.xy).T for line in path_lines])
    center_map = np.mean(all_coords, axis=0)

    def line_midpoint(line):
        x, y = line.xy
        return np.mean(x), np.mean(y)

    distances = [np.linalg.norm(np.array(line_midpoint(line)) - center_map) for line in path_lines]
    start_index = int(np.argmin(distances))

    path_lines = path_lines[start_index:] + path_lines[:start_index]
    segment_lengths = segment_lengths[start_index:] + segment_lengths[:start_index]
    path_lines_sampled = path_lines[::sampling_factor]

    fig, ax = plt.subplots(figsize=(12, 12))
    gdf.plot(ax=ax, color="lightgray", linewidth=0.4)
    
    title = os.path.splitext(os.path.basename(output_path))[0].capitalize()
    ax.set_title(f"Drone Path - {title}", fontsize=16)
    
    ax.set_axis_off()

    cumulative_x = []
    cumulative_y = []
    line, = ax.plot([], [], color="blue", linewidth=2)
    info_text = ax.text(0.02, 0.98, '', transform=ax.transAxes, fontsize=12, color="black", va='top')

    def init():
        line.set_data([], [])
        info_text.set_text('')
        return line, info_text

    def update(frame):
        geom = path_lines_sampled[frame]
        x, y = geom.xy
        cumulative_x.extend(x)
        cumulative_y.extend(y)
        line.set_data(cumulative_x, cumulative_y)

        partial_distance = sum(segment_lengths[:frame+1])
        partial_distance_km = partial_distance / 1000
        partial_time = partial_distance_km / 40  # vitesse drone
        info_text.set_text(f"Distance: {partial_distance_km:.2f} km")
        return line, info_text

    ani = animation.FuncAnimation(
        fig, update, frames=len(path_lines_sampled),
        init_func=init, blit=True, interval=10, repeat=False
    )

    total_distance_km = round(total_distance / 1000, 2)
    cost_per_km = round(0.01 * total_distance_km, 2)
    ani.save(output_path, writer="ffmpeg", fps=60)

    with open(result_path, "a", encoding="utf-8") as f:
        f.write(f"Drone information saved: {output_path}\n")
        f.write(f"Distance covered: {total_distance_km} km\n")
        f.write(f"Total time: ~ {round(total_distance_km / 40)}h\n")
        f.write(f"Total cost: {100 + cost_per_km} $\n")
        f.write(f"~~~~~~~~~~~~~~\n")
    return total_distance_km, cost_per_km

