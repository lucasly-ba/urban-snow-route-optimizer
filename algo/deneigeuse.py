import geopandas as gpd
import matplotlib.pyplot as plt
import networkx as nx
from shapely.geometry import LineString, Point
import numpy as np
import json
from math import dist
import matplotlib.animation as animation
from typing import List, Tuple, Dict

def generate_deneigeuse_output(geojson_path: str, output_path: str = "deneigeuse.mp4", num_deneigeuses: int = 3):
    gdf = gpd.read_file(geojson_path)
    gdf = gdf[gdf.geometry.type == 'LineString']

    G = nx.DiGraph()

    for idx, row in gdf.iterrows():
        line: LineString = row.geometry
        coords = np.array(line.coords)
        if len(coords) < 2:
            continue
        
        start = tuple(coords[0])
        end = tuple(coords[-1])
        name = row.get("ODONYME") or row.get("NOM_VOIE") or "Rue inconnue"
        length = np.sum(np.linalg.norm(coords[1:] - coords[:-1], axis=1)) * 111000
        
        is_one_way = row.get("SENS_UNIQUE", False)
        
        if not is_one_way:
            G.add_edge(start, end, geometry=line, name=name.strip(), length=round(length, 1))
            G.add_edge(end, start, geometry=LineString(list(reversed(line.coords))), 
                      name=name.strip(), length=round(length, 1))
        else:
            G.add_edge(start, end, geometry=line, name=name.strip(), length=round(length, 1))

    components = list(nx.strongly_connected_components(G))
    components.sort(key=len, reverse=True)
    
    component_graphs = []
    for component in components:
        subgraph = G.subgraph(component).copy()
        if subgraph.number_of_edges() > 0:
            component_graphs.append(subgraph)

    def divide_graph_for_deneigeuses(graph: nx.DiGraph, num_deneigeuses: int) -> List[nx.DiGraph]:
        if graph.number_of_edges() == 0:
            return [nx.DiGraph() for _ in range(num_deneigeuses)]

        deneigeuse_graphs = [nx.DiGraph() for _ in range(num_deneigeuses)]
        center_node = max(graph.nodes(), key=lambda x: graph.degree(x))
        distances = nx.single_source_shortest_path_length(graph, center_node)
        sorted_nodes = sorted(distances.items(), key=lambda x: x[1])
        
        nodes_per_zone = len(sorted_nodes) // num_deneigeuses
        remaining_nodes = len(sorted_nodes) % num_deneigeuses
        
        zone_nodes = [[] for _ in range(num_deneigeuses)]
        current_zone = 0
        nodes_assigned = 0
        
        for node, _ in sorted_nodes:
            zone_nodes[current_zone].append(node)
            nodes_assigned += 1
            
            if nodes_assigned >= nodes_per_zone + (1 if current_zone < remaining_nodes else 0):
                current_zone = (current_zone + 1) % num_deneigeuses
                nodes_assigned = 0
        
        for i, nodes in enumerate(zone_nodes):
            subgraph = graph.subgraph(nodes).copy()
            
            for u, v, data in graph.edges(data=True):
                if u in nodes and v in nodes:
                    deneigeuse_graphs[i].add_edge(u, v, **data)
            
            if not nx.is_strongly_connected(deneigeuse_graphs[i]):
                components = list(nx.strongly_connected_components(deneigeuse_graphs[i]))
                
                for j in range(len(components) - 1):
                    comp1 = components[j]
                    comp2 = components[j + 1]
                    
                    min_path = None
                    min_length = float('inf')
                    
                    for node1 in comp1:
                        for node2 in comp2:
                            try:
                                path = nx.shortest_path(graph, node1, node2)
                                path_length = sum(graph.get_edge_data(path[k], path[k+1])['length'] 
                                                for k in range(len(path)-1))
                                
                                if path_length < min_length:
                                    min_length = path_length
                                    min_path = path
                            except nx.NetworkXNoPath:
                                continue
                    
                    if min_path:
                        for k in range(len(min_path) - 1):
                            edge_data = graph.get_edge_data(min_path[k], min_path[k + 1])
                            if edge_data:
                                deneigeuse_graphs[i].add_edge(min_path[k], min_path[k + 1], **edge_data)
        
        return deneigeuse_graphs

    all_deneigeuse_graphs = []
    for i, component_graph in enumerate(component_graphs):
        if i == 0:
            graphs = divide_graph_for_deneigeuses(component_graph, num_deneigeuses)
        else:
            graphs = divide_graph_for_deneigeuses(component_graph, 1)
        all_deneigeuse_graphs.extend(graphs)

    def calculate_circuit(graph: nx.DiGraph) -> List[Tuple]:
        if graph.number_of_edges() == 0:
            return []
            
        if not nx.is_strongly_connected(graph):
            largest_cc = max(nx.strongly_connected_components(graph), key=len)
            graph = graph.subgraph(largest_cc).copy()
            
        while not nx.is_eulerian(graph):
            for node in graph.nodes():
                in_degree = graph.in_degree(node)
                out_degree = graph.out_degree(node)
                
                if in_degree != out_degree:
                    for other in graph.nodes():
                        if other != node:
                            other_in = graph.in_degree(other)
                            other_out = graph.out_degree(other)
                            
                            if (in_degree < out_degree and other_in > other_out) or \
                               (in_degree > out_degree and other_in < other_out):
                                if in_degree < out_degree:
                                    for u, v, data in graph.edges(data=True):
                                        graph.add_edge(other, node, **data)
                                        break
                                else:
                                    for u, v, data in graph.edges(data=True):
                                        graph.add_edge(node, other, **data)
                                        break
                                break
                    break
            
            if nx.is_eulerian(graph):
                break
            
            components = list(nx.strongly_connected_components(graph))
            if len(components) > 1:
                for i in range(len(components) - 1):
                    comp1 = components[i]
                    comp2 = components[i + 1]
                    
                    min_path = None
                    min_length = float('inf')
                    
                    for node1 in comp1:
                        for node2 in comp2:
                            try:
                                path = nx.shortest_path(graph, node1, node2)
                                path_length = sum(graph.get_edge_data(path[k], path[k+1])['length'] 
                                                for k in range(len(path)-1))
                                
                                if path_length < min_length:
                                    min_length = path_length
                                    min_path = path
                            except nx.NetworkXNoPath:
                                continue
                    
                    if min_path:
                        for k in range(len(min_path) - 1):
                            edge_data = graph.get_edge_data(min_path[k], min_path[k + 1])
                            if edge_data:
                                graph.add_edge(min_path[k], min_path[k + 1], **edge_data)
        
        return list(nx.eulerian_circuit(graph))

    deneigeuse_circuits = [calculate_circuit(g) for g in all_deneigeuse_graphs]

    fig, ax = plt.subplots(figsize=(12, 12))
    gdf.plot(ax=ax, color="lightgray", linewidth=0.4)
    ax.set_axis_off()

    colors = ['red', 'blue', 'green', 'purple', 'orange', 'brown']
    lines = [ax.plot([], [], color=colors[i % len(colors)], linewidth=2)[0] 
             for i in range(len(all_deneigeuse_graphs))]

    cumulative_x = [[] for _ in range(len(all_deneigeuse_graphs))]
    cumulative_y = [[] for _ in range(len(all_deneigeuse_graphs))]

    def init():
        for line in lines:
            line.set_data([], [])
        return lines

    def update(frame):
        for i in range(len(all_deneigeuse_graphs)):
            if i < len(deneigeuse_circuits) and frame < len(deneigeuse_circuits[i]):
                u, v = deneigeuse_circuits[i][frame]
                edge_data = all_deneigeuse_graphs[i].get_edge_data(u, v)
                if edge_data and 'geometry' in edge_data:
                    x, y = edge_data['geometry'].xy
                    cumulative_x[i].extend(x)
                    cumulative_y[i].extend(y)
                    lines[i].set_data(cumulative_x[i], cumulative_y[i])
        return lines

    max_frames = max(len(circuit) for circuit in deneigeuse_circuits) if deneigeuse_circuits else 0

    ani = animation.FuncAnimation(
        fig, update, frames=max_frames,
        init_func=init, blit=True, interval=10, repeat=False
    )

    ani.save(output_path, writer="ffmpeg", fps=60)

    total_distances = []
    for circuit in deneigeuse_circuits:
        distance = 0
        for u, v in circuit:
            edge_data = G.get_edge_data(u, v)
            if edge_data and 'length' in edge_data:
                distance += edge_data['length']
        total_distances.append(round(distance / 1000, 2))

    print(f"Trajet des déneigeuses sauvegardée : {output_path}")

    return (sum(total_distances), max(total_distances))







