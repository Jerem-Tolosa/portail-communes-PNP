# Portrait des communes du Parc national des Pyrénées

Carte en ligne répondant à la commande du conseil d'administration du Parc :
quelles communes ont du territoire dans le Parc (cœur ou aire d'adhésion),
combien d'habitants elles comptent, et quelle part de leur territoire est en
cœur de Parc

## Fichiers :

- `index.html` — la page (structure seule)
- `style.css` — la mise en page, le panneau légende, la fiche, le mode téléphone
- `main.js` — la carte MapLibre (module)
- `preparer_donnees.py` — le script qui produit les données depuis le zip du TP
- `donnees/communes_parc.pmtiles` — les données tuilées lues par la carte
- `serveur.py` — serveur de test local (réponses par plages, statut 206)

## Mise en place :

Lancer en local : `python3 serveur.py 5000` depuis ce dossier, puis ouvrir
`http://localhost:5000/`. Publier : pousser ce dossier dans un dépôt GitHub
public et activer GitHub Pages (Settings > Pages) — l'adresse sera
`https://<identifiant>.github.io/<depot>/` ; GitHub Pages répond aux requêtes
par plages, le PMTiles s'y lit comme en local.

## Choix :

**Quelles communes.** Une commune est retenue si **au moins 1 % de son
territoire est dans le Parc** (cœur ou aire d'adhésion). Le calcul se fait sur
le tracé à pleine précision (`communes_precis`), en Lambert-93 (EPSG:2154, unité
le mètre) : le tracé généralisé fait « toucher » le Parc à des communes qui ne
le touchent pas en réalité. 65 communes sont retenues ; 42 communes entre 0 et
1 % sont écartées (leur liste est imprimée par le script). La règle alternative
« toute intersection > 0 » donnerait 107 communes, mais 42 d'entre elles ont
moins de 1 % de leur territoire dans le Parc — invisible à l'échelle de la
carte et peu parlant pour des élus.

**Quelle représentation pour quelle donnée.**

- La **part de territoire en cœur** est un taux : elle est représentée par une
  **choroplèthe en 5 classes** aux seuils ronds 10 %, 25 %, 50 % (gris = 0 %,
  aire d'adhésion seule ; dégradé de orange de plus en plus soutenu). Les
  seuils sont lus sur la distribution : 54 communes à 0 %, puis 3, 3, 4 et 1
  commune(s) dans chaque classe.
- La **population** est un effectif : elle est représentée par des **cercles
  dont l'aire est proportionnelle à la population** (rayon ∝ √population), un
  point par commune posé sur son point représentatif.
- Le **cœur et l'aire d'adhésion** sont des limites : aplat vert transparent et
  contour tireté.

**Technique.** Les données sont tuilées en un seul fichier PMTiles (GDAL,
`ogr2ogr -f PMTiles`, zooms 6 à 16, `-preserve_fid` pour garder l'identifiant de
chaque entité) ; la carte les lit **par plages** grâce au protocole `pmtiles://`
(12 requêtes en statut 206 constatées en test), sur le fond vectoriel Plan IGN.
La légende est écrite à la main en HTML avec les mêmes couleurs que la carte.
Sur téléphone (≤ 640 px), le panneau passe en bas de l'écran et se replie.

## Contrôles :

Tous ces chiffres sont imprimés par `python3 preparer_donnees.py`, qui se
relance sans erreur depuis ce dossier :

- sélection : **65 communes** (≥ 1 % du territoire dans le Parc), identique
  sur les deux tracés au seuil de 1 % ; 42 communes entre 0 et 1 % écartées ;
- **65 points représentatifs**, tous vérifiés dans leur commune
  (`representative_point` + `within`) ;
- somme des surfaces en cœur des 65 communes = **315,5 km²** (cœur total :
  458,1 km², voir Limites) ;
- population des communes retenues = **29 463 hab** (contre 930 926 pour 64+65) ;
  max = 7 060 hab (Bagnères-de-Bigorre) ; part maximale dans le Parc = 100,0 % ;
- **11 communes** ont du territoire en cœur ; classes : 54 / 3 / 3 / 4 / 1 ;
- le PMTiles fait **3,02 Mo** ; lu par ogrinfo (couches `communes`, `points`,
  `coeur`, `aire`, EPSG:3857, identifiants `mvt_id` conservés) ;
- le tuilage découpe les entités aux bords des tuiles : les entités lues dans
  les tuiles (72 au zoom 6, 11 317 au zoom 16) sont des morceaux, les décomptes
  se font sur la donnée (65 communes), jamais dans les tuiles ;
- test en navigateur headless : 4 couches rendues (78 morceaux de communes,
  65 points, cœur, aire à l'ouverture), clic sur une commune → fiche correcte,
  survol → `feature-state` posé, **0 erreur console**, 12 requêtes PMTiles en
  206 ; captures desktop 1280×800 et mobile 390×844 analysées (couleurs des
  classes, cœur, légende présentes).

## Limites :

- Le cœur du Parc s'étend aussi sur la **Haute-Garonne (31)**, absente du zip :
  142,6 km² du cœur (458,1 − 315,5) ne sont dans aucune commune 64/65 et ne
  figurent pas sur la carte.
- La carte montre la population **de chaque commune**, pas le nombre
  d'habitants **vivant dans le Parc** : il faudrait une population localisée
  (adresses ou îlots INSEE) pour répondre à cette autre question.
- La population est celle de **2022** (INSEE, population municipale), sans
  date ultérieure disponible dans les données.
- L'affichage utilise le tracé généralisé : les limites communales sont
  simplifiées de quelques mètres ; les parts, elles, sont calculées sur le
  tracé à pleine précision.
- Aux bas zooms, le tuilage simplifie et peut écarter ce qui tient sous le
  pixel ; aux hauts zooms, les entités sont découpées en morceaux aux bords
  des tuiles (mêmes attributs, géométrie en plusieurs parties).
- Le fond Plan IGN et les bibliothèques (unpkg) demandent une connexion
  internet.

## Journal de bord :

1. `fiona` absent de l'environnement : remplacé par `pyogrio` pour lister les couches du GeoPackage.
2. Première fiche affichait « Territoire dans le Parc 100,47 % » (Arras-en-Lavedan) : les parts étaient rapportées au champ `surface_km2` (tracé plein) alors que l'intersection était faite sur le tracé généralisé. Corrigé : dénominateur = aire du tracé intersecté ; contrôle `max <= 100` ajouté (100,0 % au final).
3. La sélection « intersection > 0 » donnait 111 communes sur le tracé généralisé contre 107 sur le tracé précis : 6 artefacts de généralisation. Corrigé : sélection au seuil de 1 % calculée sur `communes_precis`.
4. `python3` bloqué en commande directe dans le terminal de l'agent : scripts lancés via des processus en arrière-plan.
5. `python -m http.server` ne répond pas aux plages (PMTiles illisible) : utilisation de `serveur.py`, statut 206 vérifié par curl.
6. Le navigateur demandait un `favicon.ico` en 404 : `<link rel="icon" href="data:,">` ajouté, la console reste propre.
7. Le PMTiles ne se lisait pas au premier essai : régénéré avec `-preserve_fid` après lecture du cours S4 (sans identifiant, pas de survol par `feature-state`).
8. Test headless : le premier clic tombait sur le panneau légende (pixel x > 968) au lieu de la carte — test refait hors du panneau, popup correcte.
9. Puppeteer : le binaire chrome-headless-shell n'était pas téléchargé (installation interrompue) — téléchargé manuellement depuis Chrome for Testing.
10. Les entités comptées dans les tuiles dépassaient 65 (jusqu'à 11 317 au zoom 16) : c'est le découpage aux bords des tuiles, pas des doublons — décomptes faits sur la donnée, comme le cours S4 le demande.

## Sources :

- Communes (tracés) : IGN, ADMIN EXPRESS COG CARTO PE / COG, édition 2026, WFS Géoplateforme.
- Population : INSEE, population municipale 2022 (reprise d'ADMIN EXPRESS).
- Cœur et aire d'adhésion : DREAL Nouvelle-Aquitaine, WFS SIGENA, couche `n_enp_pn_s_r75`, validation 2024-09-15.
- Fond : Plan IGN © IGN (Géoplateforme). Licence Ouverte 2.0 (Etalab).
