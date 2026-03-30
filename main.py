from algo.deneigeuse import generate_deneigeuse_output
from drone.src.split_quartiers import split_quartiers
from drone.src.split_quartiers import clean_data
from drone.src.split_quartiers import print_quartiers
from drone.src.drone_solutions import drone
from algo.cout import calculer_cout, calculer_temps
import os, sys
from pathlib import Path

def clean_and_split_data(geojson_file, output_dir):
    name_clean_data = clean_data(geojson_file)
    print(f"Data has been cleaned : {name_clean_data}")
    split_quartiers(name_clean_data, output_dir)
    print("Districts JSON have been created")
    print_quartiers(output_dir)

def deneigeuse():
    if len(sys.argv) != 2:
        print("Usage: python main.py <fichier_quartier.json>")
        sys.exit(1)

    fichier_quartier = sys.argv[1]
    nom_quartier = sys.argv[1].split("/")[-1].split(".")[0]
    
    if not os.path.exists(fichier_quartier):
        print(f"Erreur: Le fichier {fichier_quartier} n'existe pas.")
        sys.exit(1)

    while True:
        try:
            max_deneigeuses = int(input("Entrez le nombre maximum de déneigeuses: "))
            break
        except ValueError:
            print("Veuillez entrer un nombre valide.")

    while True:
        try:
            type_deneigeuse = int(input("Entrez le type de déneigeuse (1 ou 2): "))
            if type_deneigeuse in [1, 2]:
                break
            print("Le type doit être 1 ou 2.\n")
        except ValueError:
            print("Veuillez entrer un nombre valide.")

    if type_deneigeuse == 1:
        vitesse_kmh = 10
        cout_location = 500
        cout_km = 1.1
        cout_horaire = 1.1
    else:
        vitesse_kmh = 20
        cout_location = 800
        cout_km = 1.3
        cout_horaire = 1.3

    
    for i in range(1, max_deneigeuses + 1):
        print(f"\nEstimation pour {i} deneigeuses:")

        (nb_kilometres, max_kilometres) = generate_deneigeuse_output(
            fichier_quartier,
            f"output/{nom_quartier}_{i}.mp4",
            num_deneigeuses=i
        )

        print(f"Distance parcour: {nb_kilometres}km")
        temps = calculer_temps(vitesse_kmh, max_kilometres)
        print(f"Temps total: {round(temps, 2)}h")
        cout = calculer_cout(i, cout_location, cout_km, nb_kilometres, temps, cout_horaire)
        print(f"Coût total: {round(cout, 2)}€")

if __name__ == "__main__":
    #geojson_file = "data/montreal_geobase.json"
    #output_dir = "data/quartiers"
    #clean_and_split_data(geojson_file, output_dir)
    if (sys.argv[1] == "drone"):
        drone()
    else:
        deneigeuse()
