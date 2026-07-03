# Appareils et fonctionnalités supportés

Détail par type d’appareil et entités Home Assistant créées. L’intégration détecte les appareils via leurs **capabilities** API (comme l’app mobile), pas seulement par modèle.

Version de référence : **1.5.0**

## Périmètre

Cette intégration couvre **uniquement l'écosystème Enki / Leroy Merlin** : Lexman, Equation, Inspire, Noirot, Edisio, Eglo, Sedea, Evology, Nodon, ACOVA, Envertech, etc.

**Important :** beaucoup de ces appareils utilisent **Zigbee en radio** via la box Enki — c'est normal et ils restent dans le périmètre. En revanche, tout **Zigbee tiers** appairé sur la box (Sonoff, Tuya, Aqara, IKEA, …) ou tout nœud **sans fabricant Enki connu** est **ignoré** à la découverte : intégrez-les via **Zigbee2MQTT** ou **ZHA**, pas ce dépôt.

## Ventilateurs Inspire (Siroco+, Aruba+, Cadix, Radix, …)

**Entités HA :** ventilateur + lumière (kit LED)

| Fonction | Détail |
|----------|--------|
| Marche / arrêt | Vitesse 0 ou coupure moteur |
| Vitesse | 6 niveaux (mapping pourcentage HA) |
| Sens de rotation | Été (brise descendante) / hiver (déstratification) |
| Modes | Manuel, brise, ventilation, boost, auto, nuit (selon modèle) |

Le ventilateur et sa lumière sont **indépendants** : allumer l’un n’allume pas l’autre.

## Luminaires Enki (Eglo, Lexman, …)

**Entité HA :** lumière

| Fonction | Détail |
|----------|--------|
| Marche / arrêt | ON / OFF |
| Luminosité | Selon modèle |
| Blanc variable | Température de couleur (Kelvin), selon modèle |

## Prises, relais et interrupteurs (Edisio, Equation, …)

**Entité HA :** lumière ON/OFF (API `switch-electrical-power`)

| Modèle / type | Statut |
|---------------|--------|
| Prises Edisio | ✅ ON/OFF |
| Relais ON/OFF Equation ([profil](./devices/63a053851a423d4a245a877c.json)) | ✅ ON/OFF |

Les nœuds multi-circuits peuvent créer **une entité par circuit** (endpoint BFF). Conso (`check_electrical_consumption`) et timers : pas encore exposés.

## Panneaux solaires (Envertech-Lexman)

**Entité HA :** capteur de production (W)

| Fonction | Détail |
|----------|--------|
| Production instantanée | Valeur lue sur le dashboard BFF |

## Capteurs Enki (Lexman, Sedea, …)

Portage des micro-services documentés par [StephaneBranly/ha-enki](https://github.com/StephaneBranly/ha-enki).

### Mouvement / ouverture / vibration

**Entités HA :** `binary_sensor`

| Capabilité API | Entité |
|----------------|--------|
| `check_motion_detection` | Mouvement |
| `check_contact_sensor_state` | Contact (ouvert / fermé) |
| `check_vibration_detection` | Vibration |

### Température / humidité / batterie

**Entités HA :** `sensor`

| Capabilité API | Entité |
|----------------|--------|
| `check_current_temperature` | Température (°C) |
| `check_current_humidity` | Humidité (%) |
| `check_battery_health` | Batterie (%, mapping Enki) |

Thermomètres **Sedea** (écran) : température, humidité, batterie — même API que les autres capteurs Enki.

### Sirène Lexman

**Entité HA :** `switch` (ON/OFF via `switch_siren_status`)

### Réglages capteur contact

**Entités HA :** `switch` (activation détection), `number` (sensibilité vibration 1–5)

### Fuite d'eau (Lexman)

**Entités HA :** `binary_sensor` (fuite), `sensor` (batterie)

**Profil referentiel :** [651eada55b3a798ef6b6bc5c.json](./devices/651eada55b3a798ef6b6bc5c.json)

| Capability | Entité HA |
|------------|-----------|
| `check_water_sensor_state` | Fuite d'eau (humidité) |
| `check_battery_health` | Batterie |

## Chauffage

| Modèle | Entités HA | Profil |
|--------|------------|--------|
| Fil pilote Equation | `select` (Confort, Éco, Hors gel, Off) | [63a054c81a423d4a245a877e.json](./devices/63a054c81a423d4a245a877e.json) |
| Radiateur Noirot | `climate` (consigne, action chauffe), `binary_sensor` fenêtre / présence, `switch` modes détection | [67a4b12bae1eca4709a45680.json](./devices/67a4b12bae1eca4709a45680.json) |

**Clés API gateway** (`ENKI_HEATING_API_KEY`, `ENKI_WATER_SENSOR_API_KEY` dans `const.py`) : à capturer depuis l'app Enki lors d'une commande chauffage ou lecture capteur fuite — même principe que les volets ([API.md](API.md)). Sans clé, les entités apparaissent mais restent sans état jusqu'à la prochaine release incluant la clé.

Catalogue complet : [docs/devices/README.md](./devices/README.md)

## Volets roulants — beta (Evology, Nodon, …)

**Entité HA :** cover « Volet (beta) »

| Fonction | Détail |
|----------|--------|
| Ouverture / fermeture | Commandes cover HA |
| Position | 0–100 % (si l’API motorisation répond) |

Support **expérimental** : retours de testeurs bienvenus via [feature request](https://github.com/cyrilcolinet/enki-integration-hass/issues/new?template=feature_request.yml).

### Pour les testeurs

Si vous avez des volets Enki (Evology, Nodon, …) et Home Assistant, votre retour aide à stabiliser cette fonctionnalité. **Aucune manipulation réseau sur le téléphone n’est requise.**

1. **Mettre à jour** l’intégration Enki en **v1.2.0** ou plus récent ([release](https://github.com/cyrilcolinet/enki-integration-hass/releases)) via HACS, puis **redémarrer** Home Assistant.
2. **Vérifier** que vos volets apparaissent en entité **« Volet (beta) »** (Paramètres → Appareils et services → Enki).
3. **Tester** depuis HA : ouvrir, fermer, positionner — et comparer avec l’**app mobile Enki** (même compte).
4. **Remonter le résultat** sur GitHub :
   - **Ça marche** : modèle de volet + version HA + version intégration (issue ou commentaire sur une discussion volets).
   - **Ça ne marche pas** : copier un extrait des **journaux** HA filtrés sur `enki` (Paramètres → Système → Journaux). Pas besoin de partager votre mot de passe Enki.

**Si les entités existent mais ne répondent pas**, il manque probablement encore la clé technique côté API motorisation Leroy Merlin. Ce n’est pas un réglage à faire chez vous : dès qu’un contributeur la récupère, elle sera incluse dans une **prochaine mise à jour** pour tout le monde.

Pour les personnes à l’aise avec le débogage réseau (proxy, certificats) : [guide contributeur — clé API volets](BETA_VOLETS_KEY.md).

## Fonctionnalités transverses

- **Auth OAuth** — refresh token, sessions plus stables
- **Télémétrie opt-in** — notification pour appareils inconnus, lien GitHub pré-rempli (rien n’est envoyé sans clic)
- **Diagnostics** — export JSON anonymisé depuis l’UI Enki

## En cours / non supporté

| Statut | Appareils |
|--------|-----------|
| Bientôt | Radiateurs ACOVA ARLAN (même API heating si capabilities compatibles) |
| Non planifié | Alarme Enki (pas d’API identifiée) |
| Hors périmètre | Box Enki, appairage, compte Leroy Merlin → [support Enki](https://support.enki-home.com/) |

Documentation API : [API.md](API.md)
