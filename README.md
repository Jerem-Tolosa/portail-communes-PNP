# Portrait des communes du Parc national des Pyrénées

Carte en ligne répondant à la commande du conseil d'administration du Parc : quelles communes ont du territoire dans le Parc (cœur ou aire d'adhésion), combien d'habitants elles comptent, et quelle part de leur territoire est en cœur de Parc.

## Fichiers

- `index.html` — la page (structure seule)
- `style.css` — la mise en page, la légende, la fiche, le mode téléphone
- `main.js` — la carte MapLibre (module)
- `preparer_donnees.py` — le script qui produit les données depuis le zip du TP
- `donnees/communes_parc.pmtiles` — les données tuilées lues par la carte
- `serveur.py` — serveur de test local

## Mise en place

En local : `python3 serveur.py 5000`, puis ouvrir `http://localhost:5000/`.
Pour publier : pousser le dossier dans un dépôt GitHub public et activer GitHub Pages (Settings > Pages) ; l'adresse sera `https://<identifiant>.github.io/<depot>/`.

## Choix

**Quelles communes.** Une commune est retenue si au moins 1 % de son territoire est dans le Parc, calculé sur le tracé à pleine précision (le tracé généralisé fait « toucher » le Parc à des communes qui ne le touchent pas en réalité). 65 communes sont retenues, les autres sont écartées car leur part dans le Parc est trop faible pour être visible et parlante sur la carte.

**Quelle représentation pour quelle donnée.**

- La part de territoire en cœur est un taux : choroplèthe en 5 classes (gris = aire d'adhésion seule, dégradé d'orange de plus en plus soutenu).
- La population est un effectif : cercles d'aire proportionnelle à la population, un point par commune.
- Le cœur et l'aire d'adhésion : aplat vert transparent et contour tireté.

**Technique.** Les données sont tuilées en un seul fichier PMTiles (GDAL, `ogr2ogr -f PMTiles`), lu par la carte par plages grâce au protocole `pmtiles://`, sur le fond vectoriel Plan IGN. La légende est écrite à la main en HTML avec les mêmes couleurs que la carte. Sur téléphone (≤ 640 px), le panneau passe en bas de l'écran et se replie.

## Contrôles

Tous ces chiffres sont imprimés par `python3 preparer_donnees.py`, qui se relance sans erreur depuis ce dossier :

- sélection : **65 communes**, toutes avec leurs points représentatifs vérifiés ;
- population des communes retenues : **29 463 hab** ; part maximale dans le Parc : **100 %** ;
- **11 communes** ont du territoire en cœur ;
- le PMTiles fait **3 Mo** et se lit correctement (couches, projection, identifiants) ;
- test en navigateur headless : 4 couches rendues à l'ouverture, clic sur une commune → fiche correcte, survol actif, **0 erreur console**.

## Limites

- Le cœur du Parc s'étend aussi sur la Haute-Garonne (31), absente du zip : cette partie ne figure pas sur la carte.
- La carte montre la population de chaque commune, pas le nombre d'habitants vivant dans le Parc : il faudrait une population localisée (adresses ou îlots INSEE).
- La population est celle de 2022 (INSEE, population municipale).
- L'affichage utilise le tracé généralisé ; les parts, elles, sont calculées sur le tracé à pleine précision.
- Le fond Plan IGN et les bibliothèques (unpkg) demandent une connexion internet.

## Journal de bord

1. `fiona` absent de l'environnement : remplacé par `pyogrio` pour lister les couches du GeoPackage.
2. La fiche affichait parfois une part supérieure à 100 % : les parts étaient rapportées au mauvais tracé. Corrigé, avec un contrôle `max <= 100` ajouté.
3. La sélection « toute intersection > 0 » incluait des communes qui ne touchent pas réellement le Parc (artefacts de généralisation) : sélection au seuil de 1 % sur le tracé précis.
4. `python -m http.server` ne répond pas aux plages (PMTiles illisible) : utilisation de `serveur.py`.
5. Le PMTiles ne se lisait pas au premier essai : régénéré avec `-preserve_fid` (sans identifiant, pas de survol possible).
6. Favicon en 404 : corrigé, la console reste propre.

## Sources

- Communes (tracés) : IGN, ADMIN EXPRESS COG CARTO PE / COG, édition 2026, WFS Géoplateforme.
- Population : INSEE, population municipale 2022.
- Cœur et aire d'adhésion : DREAL Nouvelle-Aquitaine, WFS SIGENA, couche `n_enp_pn_s_r75`.
- Fond : Plan IGN © IGN (Géoplateforme). Licence Ouverte 2.0 (Etalab).