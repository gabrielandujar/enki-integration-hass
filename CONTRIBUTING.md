# Contribuer

Merci de prendre le temps de contribuer. Ce dépôt vise une intégration Home Assistant fiable, testée et maintenable.

## Avant de coder

1. Vérifier les [issues ouvertes](https://github.com/cyrilcolinet/enki-integration-hass/issues) — éviter le doublon
2. Pour un nouvel appareil Enki : ouvrir une **feature request** avec le output de `scripts/discover_devices.py` (sans mot de passe)
3. Lire [docs/API.md](docs/API.md) pour le contexte API

## Environnement local

```bash
git clone https://github.com/cyrilcolinet/enki-integration-hass.git
cd enki-integration-hass
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
```

## Qualité attendue

Avant toute PR :

```bash
ruff check .
ruff format .
pytest tests/unit -v
```

La CI exécute la même chose + Hassfest + HACS validation.

## Pull requests

- Une PR = un sujet (bugfix, feature, docs)
- Message de commit en anglais ou français, impératif (`fix:`, `feat:`, `docs:`)
- Tests unitaires pour la logique métier ajoutée ou modifiée
- Pas de credentials, tokens ou IDs personnels dans le code ou les commits

Modèle PR : [.github/pull_request_template.md](.github/pull_request_template.md)

## Structure du code

```
custom_components/enki/
├── api.py              # Client REST Enki
├── coordinator.py      # Polling
├── fan.py / light.py   # Plateformes HA
├── helpers.py          # Mapping pur (testable sans HA)
├── config_flow.py      # UI
└── translations/       # FR + EN
```

Règle simple : logique testable sans Home Assistant dans `helpers.py` / `*_helpers.py`, pas dans les plateformes.

## Tests live (optionnels)

Copier `.env.example` → `.env`, renseigner `ENKI_*`, puis :

```bash
pytest tests/integration -m integration -v
```

Ces tests pilotent du matériel réel — à lancer manuellement ou via `workflow_dispatch` CI avec secrets configurés.

## Code de conduite

[CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md)
