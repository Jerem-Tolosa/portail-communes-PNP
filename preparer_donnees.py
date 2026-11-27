"""Prépare les données du TP « Le portrait des communes du Parc » (UE902-1).

Lit les données du dossier donnees/, calcule pour chaque commune des deux
départements (64, 65) sa part de territoire dans le Parc national des
Pyrénées et dans son cœur, sélectionne les communes qui ont du territoire
dans le Parc, calcule un point représentatif par commune, puis produit :

  - donnees/communes_parc.gpkg   : couches communes, points, coeur, aire (EPSG:2154)
  - donnees/communes_parc.pmtiles : les mêmes couches tuilées (EPSG:3857), lues
                                    par plages par la carte MapLibre (voir main.js)

Se relance sans erreur depuis le dossier du TP :  python3 preparer_donnees.py
Les décomptes se font sur la donnée, jamais dans les tuiles (cours S4, point 1).
"""
import os
import subprocess

import geopandas as gpd
import pandas as pd

DOSSIER = os.path.dirname(os.path.abspath(__file__))
DONNEES = os.path.join(DOSSIER, "donnees")
GPKG = os.path.join(DONNEES, "communes_parc.gpkg")
PMTILES = os.path.join(DONNEES, "communes_parc.pmtiles")

MINZOOM, MAXZOOM = 6, 16  # niveaux de zoom de la pyramide de tuiles


def main():
    # 1. Lecture des données d'origine
    communes = gpd.read_file(os.path.join(DONNEES, "communes_64_65.gpkg"), layer="communes")
    communes_precis = gpd.read_file(os.path.join(DONNEES, "communes_64_65.gpkg"), layer="communes_precis")
    coeur = gpd.read_file(os.path.join(DONNEES, "pnp_coeur.geojson")).to_crs(2154)
    aire = gpd.read_file(os.path.join(DONNEES, "pnp_aire_adhesion.geojson")).to_crs(2154)

    parc = aire.union_all()          # l'aire d'adhésion englobe le cœur
    coeur_u = coeur.union_all()
    assert communes.crs == "EPSG:2154" and coeur.crs == "EPSG:2154"

    # 2. Intersections, calculées en Lambert-93 (unité : le mètre). Les parts sont
    #    rapportées à l'aire du tracé utilisé pour l'intersection (et non au champ
    #    surface_km2, calculé sur l'autre tracé) : une part ne dépasse jamais 100 %.
    surf_parc_km2 = communes.intersection(parc).area / 1e6
    surf_coeur_km2 = communes.intersection(coeur_u).area / 1e6
    surf_commune_km2 = communes.geometry.area / 1e6

    communes["surf_parc_km2"] = surf_parc_km2.round(3)
    communes["surf_coeur_km2"] = surf_coeur_km2.round(3)
    communes["part_parc_pct"] = (surf_parc_km2 / surf_commune_km2 * 100).round(2)
    communes["part_coeur_pct"] = (surf_coeur_km2 / surf_commune_km2 * 100).round(2)
    assert communes["part_parc_pct"].max() <= 100.01, "une part dépasse 100 %"
    communes["statut"] = ["Cœur du Parc" if p > 0 else "Aire d'adhésion seule"
                           for p in communes["part_coeur_pct"]]

    # 3. Sélection : au moins 1 % du territoire communal dans le Parc (cœur ou aire
    #    d'adhésion). Le calcul se fait sur le tracé à pleine précision : le tracé
    #    généralisé fait toucher au Parc des communes qui ne le touchent pas (contrôle
    #    ci-dessous). Les communes entre 0 et 1 % sont écartées, liste imprimée.
    SEUIL_PCT = 1.0
    precis = communes_precis[["code_insee"]].copy()
    precis["surf_parc_km2"] = communes_precis.intersection(parc).area / 1e6
    precis["part_parc_pct"] = (precis["surf_parc_km2"]
                               / (communes_precis.geometry.area / 1e6) * 100)
    entre_0_et_seuil = precis[(precis["part_parc_pct"] > 0)
                               & (precis["part_parc_pct"] < SEUIL_PCT)]
    print(f"contrôle : {len(entre_0_et_seuil)} communes entre 0 et {SEUIL_PCT} % du territoire "
          f"dans le Parc, écartées : {sorted(entre_0_et_seuil['code_insee'])}")
    codes_retenus = set(precis.loc[precis["part_parc_pct"] >= SEUIL_PCT, "code_insee"])
    selection = communes[communes["code_insee"].isin(codes_retenus)].copy()
    print(f"sélection : {len(selection)} communes avec au moins {SEUIL_PCT} % du territoire "
          f"dans le Parc (tracé précis : {len(codes_retenus)} codes INSEE)")

    # 4. Un point représentatif par commune, garanti dans le polygone
    points = selection.copy()
    points["geometry"] = points.geometry.representative_point()
    assert points.within(selection.geometry).all(), "un point représentatif hors de sa commune"
    print(f"contrôle points : {len(points)} points représentatifs, tous dans leur commune")

    # 5. Contrôles numériques
    print(f"contrôle : somme des surfaces en cœur = "
          f"{selection['surf_coeur_km2'].sum():.1f} km2, cœur = {coeur_u.area / 1e6:.1f} km2")
    print(f"contrôle : population des communes du Parc = {int(selection['population'].sum())} hab "
          f"(pop 64+65 totale = {int(communes['population'].sum())})")
    print(f"contrôle : {int((selection['part_coeur_pct'] > 0).sum())} communes ont du territoire en cœur")
    print(f"contrôle : part max dans le Parc = {selection['part_parc_pct'].max()} % "
          f"(doit rester <= 100)")
    print(f"population max d'une commune du Parc : {int(selection['population'].max())} hab "
          f"({selection.loc[selection['population'].idxmax(), 'nom']})")
    print("distribution de part_coeur_pct (communes du Parc) :")
    print(selection["part_coeur_pct"].describe().round(2).to_string())
    classes = pd.cut(selection["part_coeur_pct"],
                     bins=[-0.01, 0, 10, 25, 50, 100],
                     labels=["0 % (aire seule)", "]0-10] %", "]10-25] %", "]25-50] %", "]50-100] %"])
    print("classes de part en cœur :")
    print(classes.value_counts().sort_index().to_string())

    # 6. Écriture du GeoPackage intermédiaire (une couche par thème)
    for fichier in (GPKG, PMTILES):
        if os.path.exists(fichier):
            os.remove(fichier)
    colonnes = ["code_insee", "nom", "departement", "population", "date_population",
                "surface_km2", "surf_parc_km2", "surf_coeur_km2",
                "part_parc_pct", "part_coeur_pct", "statut", "geometry"]
    selection[colonnes].to_file(GPKG, layer="communes")
    points[["code_insee", "nom", "departement", "population", "part_coeur_pct", "statut",
            "geometry"]].to_file(GPKG, layer="points")
    coeur[["nom", "geometry"]].to_file(GPKG, layer="coeur")
    aire[["nom", "geometry"]].to_file(GPKG, layer="aire")

    # 7. Tuilage en PMTiles par GDAL, identifiants conservés (survol de la carte)
    subprocess.run([
        "ogr2ogr", "-f", "PMTiles",
        PMTILES, GPKG,
        "-dsco", f"MINZOOM={MINZOOM}", "-dsco", f"MAXZOOM={MAXZOOM}",
        "-preserve_fid",  # chaque entité garde son identifiant : le survol en a besoin
    ], check=True)
    print(f"écrit : {PMTILES} ({os.path.getsize(PMTILES) / 1e6:.2f} Mo)")

    # 8. Contrôle du tuilage, zoom par zoom : les entités sont comptées sur la donnée
    for zoom in range(MINZOOM, MAXZOOM + 1):
        tuiles = gpd.read_file(PMTILES, layer="communes", ZOOM_LEVEL=zoom)
        print(f"zoom {zoom:2} : {len(tuiles)} entités lues dans les tuiles "
              f"(donnée : {len(selection)} communes)")


if __name__ == "__main__":
    main()
