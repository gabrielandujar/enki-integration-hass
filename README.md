# Enki pour Home Assistant

<p align="center">
  <img src="https://img.shields.io/badge/Home%20Assistant-2024.12%2B-41BDF5?style=flat-square&logo=home-assistant&logoColor=white" alt="Home Assistant" />
  <img src="https://img.shields.io/badge/HACS-Custom-orange?style=flat-square" alt="HACS" />
  <img src="https://img.shields.io/badge/License-MIT-yellow?style=flat-square" alt="MIT" />
  <img src="https://img.shields.io/badge/Maintained-yes-brightgreen?style=flat-square" alt="Maintained" />
</p>

[![Open in HACS](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=cyrilcolinet&repository=enki-integration-hass&category=integration)

Intégration personnalisée [Home Assistant](https://www.home-assistant.io/) pour piloter vos appareils **Enki** (écosystème Leroy Merlin / Adeo) depuis votre instance locale — ventilateurs de plafond **Inspire**, luminaires, et kits lumière associés.

> **Fork** — Ce dépôt est une évolution maintenue de [CyrilP/hass-enki-component](https://github.com/CyrilP/hass-enki-component). La couche API (authentification OIDC, découverte des foyers, microservices cloud) reprend la base du projet original, enrichie du support **ventilateurs Inspire / ESDK** et d’une structure moderne (tests, CI, Renovate).

---

## Appareils supportés

| Famille | Exemples | Entités Home Assistant |
|---------|----------|----------------------|
| Ventilateur de plafond ESDK | Inspire Siroco+, Aruba+ | `fan` (6 vitesses) + `light` (kit LED) |
| Luminaires Enki | Eglo V-Link, Lexman, plafonniers | `light` (ON/OFF, luminosité, température de couleur) |

Les radiateurs, volets, prises et alarmes Enki ne sont **pas encore** exposés — le script `scripts/discover_devices.py` permet d’identifier les types présents sur votre compte pour contribuer.

---

## Fonctionnalités

- Connexion cloud via les identifiants de l’**application Enki** (e-mail + mot de passe)
- Découverte automatique de tous les foyers du compte
- Ventilateur : marche/arrêt, vitesse en 6 niveaux (mapping pourcentage HA)
- Lumière (kit fan ou lampe) : ON/OFF, luminosité, blanc variable selon capacités
- Intervalle de polling configurable (10–300 s)
- Reconfiguration des identifiants depuis l’UI
- Traductions **français** et **anglais**

---

## Installation

### Via HACS (recommandé)

Conforme à la [documentation HACS pour les publishers](https://www.hacs.xyz/docs/publish/).

**Option A — lien direct** (après publication du dépôt sur GitHub)

Cliquez sur le badge **Open in HACS** en haut de ce README.

**Option B — dépôt personnalisé**

1. **HACS** → Intégrations → ⋮ → **Dépôts personnalisés**
2. URL : `https://github.com/cyrilcolinet/enki-integration-hass` — catégorie **Integration**
3. Recherchez **Enki** → **Télécharger** → redémarrer Home Assistant
4. **Paramètres** → **Appareils et services** → **Ajouter une intégration** → **Enki**

> Guide publication / store par défaut : [docs/HACS.md](docs/HACS.md)

### Installation manuelle

Copiez le dossier `custom_components/enki/` dans `config/custom_components/` puis redémarrez HA.

---

## Configuration

| Champ | Description |
|-------|-------------|
| E-mail | Compte Enki / Leroy Merlin (même que l’app mobile) |
| Mot de passe | Mot de passe du compte |

**Options** (après installation) : intervalle de rafraîchissement en secondes (défaut : 30).

> **Box Enki** requise pour la plupart des appareils Zigbee/ESDK. L’intégration utilise l’API cloud comme l’application officielle (pas de liaison locale directe).

---

## Architecture

```
custom_components/enki/
├── api.py           # Client REST (auth, discovery, commandes)
├── coordinator.py   # Polling DataUpdateCoordinator
├── fan.py           # Plateforme ventilateur
├── light.py         # Plateforme lumière (fan kit + lampes)
├── config_flow.py   # UI + options
└── ...
```

Documentation technique des endpoints : [docs/API.md](docs/API.md).

---

## Développement

### Prérequis

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
```

### Tests unitaires

```bash
pytest tests/unit -v
```

### Tests d’intégration (API réelle)

Copiez `.env.example` vers `.env` et renseignez vos identifiants + `ENKI_HOME_ID` / `ENKI_NODE_ID` (récupérables via `scripts/discover_devices.py`).

```bash
set -a && source .env && set +a
pytest tests/integration -v -m integration
```

Les tests live remettent le ventilateur et la lumière à l’arrêt en fin de session.

### Qualité

- **Ruff** — lint & format (`CI` workflow)
- **Hassfest** + **HACS** — workflow `Validate` ([doc action](https://www.hacs.xyz/docs/publish/action/))
- **Renovate** — mises à jour automatiques des dépendances et GitHub Actions

### Publier une release

```bash
git tag v1.0.0
git push origin v1.0.0
# GitHub → Releases → Publish release (déclenche release.yml + ZIP HACS)
```

---

## Crédits et ligneage

| Projet | Contribution |
|--------|----------------|
| [CyrilP/hass-enki-component](https://github.com/CyrilP/hass-enki-component) | Auth OIDC, API lighting, structure HACS d’origine |
| Reverse engineering communautaire | Microservices `api-enki-airflow-prod`, `api-enki-power-prod` pour ventilateurs ESDK |

Ce dépôt n’est **pas** affilié à Leroy Merlin, Adeo ou Enki. L’API utilisée n’est pas documentée publiquement ; elle peut évoluer sans préavis.

---

## Licence

[MIT](LICENSE) — Copyright (c) 2026 Cyril Colinet
