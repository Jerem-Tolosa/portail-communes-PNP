// Portrait des communes du Parc national des Pyrénées — la carte de la commande.
// MapLibre lit donnees/communes_parc.pmtiles par plages, grâce au protocole pmtiles://
// (la variable pmtiles vient du <script> classique de index.html).
import * as maplibregl from "https://unpkg.com/maplibre-gl@6.16.0/dist/maplibre-gl.mjs";

const protocole = new pmtiles.Protocol();
maplibregl.addProtocol("pmtiles", protocole.tile); // une adresse pmtiles://... passe par lui

// La carte, sur le fond Plan IGN, cadrée sur le Parc (ouest, sud, est, nord)
const map = new maplibregl.Map({
  container: "map", // l'identifiant du <div> qui reçoit la carte
  style: "https://data.geopf.fr/annexes/ressources/vectorTiles/styles/PLAN.IGN/standard.json",
  attributionControl: { customAttribution: "Plan IGN © IGN" }, // le style n'en déclare aucune
});
map.fitBounds([[-0.697, 42.673], [0.367, 43.178]], { animate: false, padding: 24 });
map.addControl(new maplibregl.NavigationControl(), "top-left"); // zoom et boussole
map.addControl(new maplibregl.ScaleControl(), "bottom-left"); // échelle
window.map = map; // la carte, accessible depuis la console

// Sur téléphone, la légende est repliée à l'ouverture : la carte se lit d'abord
if (window.innerWidth < 640) {
  document.getElementById("legende").removeAttribute("open");
}

// Mentions de crédit des données du PMTiles, posées sur la source (une seule fois)
const CREDITS = "Communes : IGN, ADMIN EXPRESS ; population : INSEE (2022) ; "
  + "cœur et aire d'adhésion : DREAL Nouvelle-Aquitaine";

// Couleurs des classes de part de territoire en cœur (identiques à la légende de index.html)
const COULEURS_PART_COEUR = ["#e8e8e8", "#f7fcf0", "#c7e9c0", "#74c476", "#238b45"];

map.on("load", () => { // quand le style et ses ressources sont chargés
  // Les couches du Parc se glissent sous les écritures du Plan IGN, en haut de la pile
  const couchesDuStyle = map.getStyle().layers; // de la plus basse à la plus haute
  let ecritures; // la plus basse de ces écritures
  for (let i = couchesDuStyle.length - 1; i >= 0; i--) { // du haut de la pile vers le bas
    if (couchesDuStyle[i].type !== "symbol") break; // pas une écriture : on s'arrête
    ecritures = couchesDuStyle[i].id;
  }

  // Une seule source vectorielle : le PMTiles produit par preparer_donnees.py
  map.addSource("parc", {
    type: "vector", // des tuiles vectorielles, lues par morceaux
    url: "pmtiles://donnees/communes_parc.pmtiles", // lu par le protocole, par plages (206)
    attribution: CREDITS, // mention de crédit de la source
  });

  // L'aire d'adhésion, en contour tireté
  map.addLayer({
    id: "aire",
    type: "line",
    source: "parc",
    "source-layer": "aire", // la couche « aire » du fichier PMTiles
    paint: {
      "line-color": "#006d2c",
      "line-width": 1.5,
      "line-dasharray": [3, 2], // tiret puis blanc, en largeurs de trait
    },
  }, ecritures);

  // Les communes du Parc, en classes de part de territoire en cœur de Parc.
  // Le survol passe par l'état de l'entité, désigné par son identifiant (-preserve_fid)
  map.addLayer({
    id: "communes",
    type: "fill",
    source: "parc",
    "source-layer": "communes",
    paint: {
      "fill-color": [
        "step", ["get", "part_coeur_pct"], // selon la part en cœur, en % :
        COULEURS_PART_COEUR[0], // 0 % : aire d'adhésion seule
        0.0001, COULEURS_PART_COEUR[1], // ]0-10] %
        10, COULEURS_PART_COEUR[2], // ]10-25] %
        25, COULEURS_PART_COEUR[3], // ]25-50] %
        50, COULEURS_PART_COEUR[4], // plus de 50 %
      ],
      "fill-opacity": [
        "case",
        ["boolean", ["feature-state", "survol"], false],
        0.9, 0.6, // l'entité survolée s'assombrit
      ],
      "fill-outline-color": [
        "case",
        ["boolean", ["feature-state", "survol"], false],
        "#252525", "#737373",
      ],
    },
  }, ecritures);

  // Le cœur du Parc, en aplat vert transparent, par-dessus les communes
  
  map.addLayer({
    id: "coeur",
    type: "fill",
    source: "parc",
    "source-layer": "coeur",
    paint: {
      "fill-color": "#41ab5d",
      "fill-opacity": 0.25, // aplat transparent : le fond se lit à travers
      "fill-outline-color": "#006d2c",
    },
  }, ecritures);

  // Un cercle par commune, par rapport au point existant
  map.addLayer({
    id: "points",
    type: "circle",
    source: "parc",
    "source-layer": "points",
    paint: {
      "circle-radius": ["max", 2.5, ["*", 0.21, ["sqrt", ["get", "population"]]]],
      "circle-color": "#08519c",
      "circle-opacity": 0.8,
      "circle-stroke-color": "#ffffff",
      "circle-stroke-width": 1,
    },
  }, ecritures);

  // survol commune
  let survolee = null;
  function eteindre() {
    if (survolee) {
      map.setFeatureState(
        { source: "parc", sourceLayer: "communes", id: survolee.id },
        { survol: false },
      );
    }
    survolee = null;
    map.getCanvas().style.cursor = "";
  }
  map.on("mousemove", "communes", (e) => {
    eteindre();
    survolee = e.features[0];
    if (survolee) {
      map.setFeatureState(
        { source: "parc", sourceLayer: "communes", id: survolee.id },
        { survol: true },
      );
      map.getCanvas().style.cursor = "pointer";
    }
  });
  map.on("mouseleave", "communes", eteindre);

  // La fiche d'une commune au clic (sur son aplat ou sur son cercle)

  const fmt = new Intl.NumberFormat("fr-FR");
  function fiche(props) {
    const div = document.createElement("div");
    div.className = "fiche";
    const titre = document.createElement("h3");
    const dep = props.departement === "64" ? "Pyrénées-Atlantiques" : "Hautes-Pyrénées";
    titre.textContent = `${props.nom} (${dep})`;
    div.appendChild(titre);
    const ul = document.createElement("ul");
    const lignes = [
      ["Population", `${fmt.format(props.population)} hab (${String(props.date_population).slice(0, 4)})`],
      ["Surface", `${props.surface_km2} km²`],
      ["Territoire dans le Parc", `${props.part_parc_pct} %`],
      ["dont en cœur de Parc", `${props.part_coeur_pct} %`],
      ["Statut", props.statut],
    ];
    for (const [champ, valeur] of lignes) {
      const li = document.createElement("li");
      const c = document.createElement("span");
      c.textContent = champ;
      const v = document.createElement("span");
      v.className = "valeur";
      v.textContent = valeur;
      li.append(c, v);
      ul.appendChild(li);
    }
    div.appendChild(ul);
    return div;
  }
  function auClic(e) {
    const props = e.features[0].properties;
    new maplibregl.Popup({ maxWidth: "280px" })
      .setLngLat(e.lngLat)
      .setDOMContent(fiche(props))
      .addTo(map);
  }
  map.on("click", "communes", auClic);
  map.on("click", "points", auClic);
});
