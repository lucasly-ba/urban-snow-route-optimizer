import json
import os
from unidecode import unidecode
import geopandas as gpd
import matplotlib.pyplot as plt
import networkx as nx
from shapely.geometry import LineString, Point, mapping
from math import dist

from scipy.spatial import KDTree
import numpy as np

quartiers = [
    "Outremont",
    "Verdun",
    "Anjou",
    "Rivière-des-Prairies-Pointe-aux-Trembles",
    'Le-Plateau-Mont-Royal',
    "Ahuntsic-Cartierville",
    "Côte-des-Neiges-Notre-Dame-de-Grâce",
    "Lachine",
    "LaSalle",
    "Le-Sud-Ouest",
    "L'Île-Bizard-Sainte-Geneviève",
    "Mercier-Hochelaga-Maisonneuve",
    "Montréal-Nord",
    "Pierrefonds-Roxboro",
    "Rosemont-La-Petite-Patrie",
    "Saint-Laurent",
    "Saint-Léonard",
    "Ville-Marie",
    "Villeray-Saint-Michel-Parc-Extension"
]

pieton = {
    "passage", "promenade", "jardin", "parc", "crête", "cercle", "chemin",
    "allée", "impasse", "ruelle", "terrasse", "rond-point", "place",
    "carrefour", "cours", "lane"
}

def is_pieton(properties):
    sens_circ = properties.get("SENS_CIR")
    if sens_circ == 3 or sens_circ == 4:
        return True
    typ_voie = properties.get("TYP_VOIE")
    if typ_voie is None:
        return False
    if typ_voie.lower() in pieton:
        return True
    return False

def normalize_nom(nom):
    if not nom or nom == "N/A":
        return None
    return unidecode(nom.strip().lower().replace("–", "-").replace("—", "-").replace(" ","-"))

def clean_arrondissement(arr_gch, arr_drt):
    if arr_gch is None or arr_gch == "N/A":
        return normalize_nom(arr_drt)
    return normalize_nom(arr_gch)

def clean_data(path):
    gdf = gpd.read_file(path)
    gdf = gdf[gdf.geometry.type == 'LineString']

    features = []

    for idx, row in gdf.iterrows():
        # On récupère les properties depuis GeoPandas
        properties = dict(row)
        for key in ["geometry"]:  # on retire la géométrie des properties
            properties.pop(key, None)

        # Suppression des champs inutiles
        for key in ["DEB_GCH", "FIN_GCH", "DEB_DRT", "FIN_DRT", "LIE_VOIE", "POSITION", "LIM_GCH", "LIM_DRT"]:
            properties.pop(key, None)

        if not is_pieton(properties):
            feature = {
                "type": "Feature",
                "geometry": mapping(row["geometry"]),
                "properties": properties
            }
            features.append(feature)

    name_output = "clean_montreal_geobase.json"
    output_path = os.path.join("data", name_output)
    os.makedirs("data", exist_ok=True)

    with open(output_path, "w", encoding="utf-8") as f_out:
        output_geojson = {
            "type": "FeatureCollection",
            "name": "geobase_mtl",
            "features": features
        }
        json.dump(output_geojson, f_out, indent=2)

    #print_map("", output_path)
    return "data/" + name_output

# Split en fonction des quartiers
def split_quartiers(input_path, output_dir):
    with open(input_path, "r", encoding="utf-8") as f:
        geojson_data = json.load(f)

    os.makedirs(output_dir, exist_ok=True)
    quartiers_dict = {normalize_nom(q): [] for q in quartiers}

    for feature in geojson_data["features"]:
        arr_gch = feature["properties"].get("ARR_GCH")
        arr_drt = feature["properties"].get("ARR_DRT")
        arr_name = clean_arrondissement(arr_gch, arr_drt)

        if arr_name is not None and arr_name in quartiers_dict:
            quartiers_dict[arr_name].append(feature)

    for quartier, features in quartiers_dict.items():
        output_geojson = {
            "type": "FeatureCollection",
            "name": f"geobase_mtl_{quartier}",
            "features": features
        }
        filename = quartier + ".json"
        output_path = os.path.join(output_dir, filename)
        with open(output_path, "w", encoding="utf-8") as out_f:
            json.dump(output_geojson, out_f, indent=2)

def print_map(output_dir, filename):
    geojson_path = filename if output_dir == "" else os.path.join(output_dir, filename)

    with open(geojson_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    features = data["features"]
    edges = []

    for feature in features:
        coords = feature["geometry"]["coordinates"]
        if len(coords) < 2:
            continue
        line = LineString(coords)
        start = tuple(coords[0])
        end = tuple(coords[-1])
        name = feature["properties"].get("ODONYME") or feature["properties"].get("NOM_VOIE") or "Rue inconnue"
        length = line.length * 111000
        edges.append((start, end, {
            "geometry": line,
            "name": name.strip(),
            "length": round(length, 1)
        }))

    G = nx.Graph()
    for u, v, data in edges:
        G.add_edge(u, v, **data)

    plt.figure(figsize=(10, 10))
    pos = {node: (node[0], node[1]) for node in G.nodes}
    nx.draw(G, pos, node_size=10, edge_color="gray", linewidths=0.5, with_labels=False)
    plt.title("Graphe des routes chargé")
    plt.show()

def print_quartiers(output_dir):
    for filename in os.listdir(output_dir):
        print_map(output_dir, filename)
