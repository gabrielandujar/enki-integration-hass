# Enki pour Home Assistant

<p align="center">
  <a href="https://github.com/cyrilcolinet/enki-integration-hass/actions/workflows/ci.yml"><img src="https://github.com/cyrilcolinet/enki-integration-hass/actions/workflows/ci.yml/badge.svg" alt="CI" /></a>
  <img src="https://img.shields.io/badge/Home%20Assistant-2024.12%2B-41BDF5?style=flat-square&logo=home-assistant&logoColor=white" alt="Home Assistant" />
  <img src="https://img.shields.io/badge/HACS-Custom-orange?style=flat-square" alt="HACS" />
  <img src="https://img.shields.io/badge/License-MIT-yellow?style=flat-square" alt="MIT" />
</p>

[![Open in HACS](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=cyrilcolinet&repository=enki-integration-hass&category=integration)

Intégration personnalisée [Home Assistant](https://www.home-assistant.io/) pour piloter les appareils **Enki** (Leroy Merlin / Adeo) depuis votre instance locale — ventilateurs de plafond **Inspire**, luminaires, kits lumière associés.

> Fork maintenu de [CyrilP/hass-enki-component](https://github.com/CyrilP/hass-enki-component) — API cloud Enki, support ventilateurs ESDK, tests unitaires, CI.

## Sommaire

- [Appareils supportés](#appareils-supportés)
- [Fonctionnalités](#fonctionnalités)
- [Installation](#installation)
- [Configuration](#configuration)
- [Développement](#développement)
- [Contribuer](#contribuer)
- [Crédits](#crédits)

## Appareils supportés

| Famille | Exemples | Entités HA |
|---------|----------|------------|
| Ventilateur de plafond ESDK | Inspire Siroco+, Aruba+ | `fan` + `light` (kit LED) |
| Luminaires Enki | Eglo V-Link, Lexman | `light` |

Radiateurs, volets, prises, alarmes : **pas encore** exposés. Pour aider au support, voir [Contribuer](#contribuer).

## Fonctionnalités

**Ventilateur**

- Marche / arrêt, 6 vitesses (slider HA)
- Sens de rotation été / hiver (`fan.set_direction`)
- Mode manuel / brise (`fan.set_preset_mode`)

**Lumière** (kit ventilo ou lampe)

- ON/OFF, luminosité, température de couleur selon capacités

**Intégration**

- Connexion via identifiants app Enki (e-mail + mot de passe)
- Découverte multi-foyers
- Polling configurable (10–300 s)
- Reconfiguration depuis l’UI
- FR / EN

## Installation

### HACS (recommandé)

1. **HACS** → Intégrations → ⋮ → **Dépôts personnalisés**
2. URL : `https://github.com/cyrilcolinet/enki-integration-hass` — catégorie **Integration**
3. Rechercher **Enki** → **Télécharger** → redémarrer Home Assistant
4. **Paramètres** → **Appareils et services** → **Ajouter une intégration** → **Enki**

Ou le badge **Open in HACS** en haut de page.

Guide publication HACS : [docs/HACS.md](docs/HACS.md)

### Manuelle

Copier `custom_components/enki/` dans `config/custom_components/`, redémarrer HA.

## Configuration

| Champ | Description |
|-------|-------------|
| E-mail | Compte Enki / Leroy Merlin (même que l’app mobile) |
| Mot de passe | Mot de passe du compte |

**Options** : intervalle de polling (défaut 30 s).

> Box Enki requise pour la plupart des appareils Zigbee/ESDK. L’intégration passe par l’API cloud comme l’app officielle.

## Développement

### Prérequis

- Python 3.12+
- Home Assistant 2024.12+

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
```

### Commandes

```bash
ruff check . && ruff format --check .   # lint
pytest tests/unit -v                     # tests unitaires
```

Tests live (API réelle, optionnels) :

```bash
cp .env.example .env   # renseigner ENKI_* 
set -a && source .env && set +a
pytest tests/integration -v -m integration
```

Découverte des appareils sur votre compte :

```bash
python3 scripts/discover_devices.py <email> <password>
```

### CI

Chaque push sur `main` et chaque pull request déclenche :

- Ruff (lint + format)
- Pytest (tests unitaires)
- Hassfest
- Validation HACS

Workflow : [.github/workflows/ci.yml](.github/workflows/ci.yml)

### Release

```bash
git tag v1.0.6
git push origin v1.0.6
```

Puis publier la release sur GitHub — le workflow `release.yml` attache le ZIP HACS.

## Contribuer

- [CONTRIBUTING.md](CONTRIBUTING.md) — setup, tests, PR
- [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md)
- [SECURITY.md](SECURITY.md) — signalement vulnérabilité
- Issues : bug, feature request, ou profil appareil via les templates GitHub

Documentation API (reverse engineering) : [docs/API.md](docs/API.md)

## Crédits

| Projet | Rôle |
|--------|------|
| [CyrilP/hass-enki-component](https://github.com/CyrilP/hass-enki-component) | Base auth OIDC, API lighting |
| Communauté | Microservices airflow / power pour ventilateurs ESDK |

Ce dépôt n’est **pas** affilié à Leroy Merlin, Adeo ou Enki. API non officielle — peut changer sans préavis.

## Licence

[MIT](LICENSE) — Copyright (c) 2026 Cyril Colinet
