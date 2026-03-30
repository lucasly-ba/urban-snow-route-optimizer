def calculer_temps(vitesse_kmh: float, distance_km: float) -> float:
    return distance_km / vitesse_kmh

def calculer_cout(nb_vehicules: int, cout_location: float, cout_km: float, distance_km: float, temps: float, cout_horaire: float) -> float:
    # Calcul du coût horaire en fonction du temps
    if temps <= 8:
        cout_horaire_total = temps * cout_horaire
    else:
        cout_horaire_total = (8 * cout_horaire) + ((temps - 8) * (cout_horaire + 0.2))
    
    return nb_vehicules * cout_location + (cout_km * distance_km) + cout_horaire_total