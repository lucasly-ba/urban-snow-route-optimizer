from drone.src.drone import generate_drone_output
from drone.src.solution_2 import solution2
import os
from pathlib import Path

def solution1():
    output_path = "drone/output_solution1"
    output_sol1 = "drone/results/solution1"
    i = 1
    total_distance_km = 0
    cost_per_km = 0
    max_time = 0
    for fichier in os.listdir("data/quartiers"):
        nom = output_path + "/"+fichier[:-4] + "mp4"
        (a,b) = generate_drone_output("data/quartiers" + "/" + fichier, nom, output_sol1)
        total_distance_km += a
        cost_per_km += b
        if a > max_time:
            max_time = a
        total_distance_km += a
        
        print(str(i) + " / 19 : " + fichier[:-5])
        i +=1
    
    with open(output_sol1, "a", encoding="utf-8") as f:
        f.write("\n")
        f.write("\n")
        f.write("========== RESULTS FOR SOLUTION 1 ==========")
        f.write(f"Total time: ~ {round(max_time / 40)}h\n")
        f.write(f"Total cost: {(i * 100) + cost_per_km} $\n")
        f.write(f"============================================")

    print("solution 1 finished")


def solution_all_montreal():
    data = "data/clean_montreal_geobase.json" 
    output_sol3 = "drone/results/solution3"
    output = "drone/output_solution3/Montreal.mp4"
    with open(output_sol3, "a", encoding="utf-8") as f:
        f.write("\n")
        f.write("\n")
        f.write("========== RESULTS FOR SOLUTION 3 ==========")
    generate_drone_output(data, output, output_sol3)
    print("solution 3 finished")

def drone():
    print()
    print("--- info ---")
    print("Drone speed : 40 km/h")
    print("Fixed cost: 100 $/day")
    print("Cost per Km : 0.01 $/day")
    print()
    print("Solution 1: 19 drones, 1 drone per district")
    solution1()
    print("solution 2: 10 drones, 1 drone par zone")
    solution2();
    print("solution 3: 1 drone")
    solution_all_montreal()
