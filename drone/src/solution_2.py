from drone.src.split_quartiers import print_quartiers
from drone.src.drone import generate_drone_output
import geopandas as gpd
import networkx as nx
from shapely.geometry import LineString, Point
import numpy as np
import json
from sklearn.cluster import KMeans
import os

def load_graph(geojson_path):
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

    return G

def partition_graph(G, k=10):
    nodes = np.array(list(G.nodes()))
    
    kmeans = KMeans(n_clusters=k, random_state=42).fit(nodes)
    labels = kmeans.labels_

    partitions = {i: [] for i in range(k)}

    for u, v, data in G.edges(data=True):
        u_label = kmeans.predict([u])[0]
        partitions[u_label].append((u, v, data))

    return partitions

from shapely.geometry import mapping

def save_partitions(partitions, output_dir):
    os.makedirs(output_dir, exist_ok=True)
    
    for i, edges in partitions.items():
        features = []
        for u, v, data in edges:
            line = data['geometry']
            properties = {
                "name": data["name"],
                "length": data["length"]
            }
            feature = {
                "type": "Feature",
                "geometry": mapping(line),
                "properties": properties
            }
            features.append(feature)
        geojson = {
            "type": "FeatureCollection",
            "features": features
        }
        with open(os.path.join(output_dir, f"montreal_part_{i+1}.json"), "w", encoding="utf-8") as f:
            json.dump(geojson, f, indent=2)

def solution2():
    geojson_path = "data/clean_montreal_geobase.json"
    output_dir = "data/partitions"
    output_path = "drone/output_solution2"
    output_sol2 = "drone/results/solution2"
    
    G = load_graph(geojson_path)
    partitions = partition_graph(G, 30)
    save_partitions(partitions, output_dir)
    #print_quartiers(output_dir)
    print("Découpage terminé.")
    i = 1
    total_distance_km = 0
    cost_per_km = 0
    max_time = 0
    for fichier in os.listdir("data/partitions"):
        nom = output_path + "/"+fichier[:-4] + "mp4"
        print(fichier)
        (a,b) = generate_drone_output("data/partitions" + "/" + fichier, nom, output_sol2)
        if a > max_time:
            max_time = a
        total_distance_km += a
        cost_per_km += b
        print(str(i) + " / 10 : " + fichier[:-5])
        i +=1
    
    with open(output_sol2, "a", encoding="utf-8") as f:
        f.write("\n")
        f.write("\n")
        f.write("========== RESULTS FOR SOLUTION 2 ==========")
        f.write(f"Total time: ~ {round(max_time / 40)}h\n")
        f.write(f"Total cost: {(i * 100) + cost_per_km} $\n")
        f.write(f"============================================")

    print("solution 2 finished")


