# Enki pour Home Assistant

[![Open in HACS](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=cyrilcolinet&repository=enki-integration-hass&category=integration)

Contrôlez vos appareils **Enki** (Leroy Merlin) depuis Home Assistant : ventilateurs de plafond **Inspire**, luminaires, lumière du kit ventilo.

Mêmes identifiants que l’**application mobile Enki**. Pas de box supplémentaire à configurer dans Home Assistant — la box Enki doit déjà fonctionner avec l’app.

## Feuille de route

### ✅ Supporté (v1.1.3)

| Appareil | Dans Home Assistant |
|----------|---------------------|
| Ventilateurs Inspire (Siroco+, Aruba+, Cadix, Radix, …) | Ventilateur + lumière kit |
| Luminaires Enki (Eglo, Lexman, …) | Lumière (luminosité / blanc variable) |
| Prises et interrupteurs connectés (Edisio, …) | Lumière ON/OFF (API power) |
| Panneaux solaires Envertech-Lexman | Capteur de production (W) |

| Fonctionnalité | Détail |
|----------------|--------|
| Détection par capabilities | Nouveaux appareils compatibles API pris en charge sans mise à jour de l’intégration |
| Auth OAuth | Refresh token (sessions plus stables) |
| Télémétrie opt-in | Onboarding à l’installation + notification unique pour les installs legacy ; profils anonymisés via issue GitHub |

L’intégration détecte les appareils via leurs **capabilities** API (comme l’app mobile), pas seulement par modèle.

### 🔜 Bientôt

| Appareil / sujet | Statut | Issue |
|------------------|--------|-------|
| Radiateurs ACOVA ARLAN | API identifiée, implémentation à venir | [#75](https://github.com/CyrilP/hass-enki-component/issues/75) (upstream) |
| Volets roulants Evology (EnOcean) | En étude (capabilities + scénarios) | [#53](https://github.com/CyrilP/hass-enki-component/issues/53) (upstream) |

Priorisation selon retours et contributions — [ouvrir une feature request](https://github.com/cyrilcolinet/enki-integration-hass/issues/new?template=feature_request.yml) pour voter un appareil.

### ⏳ En attente / non planifié

| Sujet | Détail |
|-------|--------|
| Alarme Enki | Pas d’API exposée identifiée pour l’instant |
| Store HACS par défaut | Dépôt custom pour l’instant ; inclusion au store global en attente de critères HACS |

### ❌ Hors périmètre

- Box Enki, appairage, compte Leroy Merlin → [support Enki](https://support.enki-home.com/)
- Appareils sans capabilities compatibles dans l’API cloud Enki

## Ce qui est supporté — détail

### Ventilateur

- Allumer / éteindre
- Régler la vitesse (6 niveaux)
- Changer le sens (été / hiver)
- Mode manuel ou mode brise

### Lumière

- Allumer / éteindre
- Luminosité et blanc variable (selon le modèle)

Le ventilateur et sa lumière sont **indépendants** : allumer l’un n’allume pas l’autre.

## Prérequis

- Home Assistant **2024.12** ou plus récent
- [HACS](https://hacs.xyz/) installé (méthode recommandée)
- Compte Enki / Leroy Merlin (e-mail + mot de passe de l’app)
- Box Enki configurée et appareils visibles dans l’app mobile

## Installation avec HACS

1. Ouvrez **HACS** → **Intégrations**
2. Menu **⋮** (en haut à droite) → **Dépôts personnalisés**
3. Collez l’URL : `https://github.com/cyrilcolinet/enki-integration-hass`
4. Catégorie : **Integration** → **Ajouter**
5. **HACS** → **Intégrations** → **Explorer et télécharger des dépôts**
6. Recherchez **Enki** → **Télécharger**
7. **Redémarrez** Home Assistant

Vous pouvez aussi cliquer sur le badge **Open in HACS** en haut de cette page.

## Ajouter l’intégration

1. **Paramètres** → **Appareils et services**
2. **Ajouter une intégration** (en bas à droite)
3. Cherchez **Enki**
4. Saisissez l’**e-mail** et le **mot de passe** de votre compte Enki (les mêmes que l’app Leroy Merlin)
5. Validez — vos appareils apparaissent après quelques secondes

## Options

**Paramètres** → **Appareils et services** → **Enki** → **Configurer**

| Option | Description |
|--------|-------------|
| Intervalle de rafraîchissement | Fréquence de mise à jour depuis le cloud (défaut : 30 secondes). Augmentez si vous voulez moins solliciter l’API. |
| Télémétrie (opt-in) | Notification quand un appareil inconnu ou non supporté est détecté ; lien GitHub pré-rempli, rien n’est envoyé sans votre clic. |

Pour **changer le mot de passe** : même menu → **Reconfigurer**.

## Utilisation dans Home Assistant

Chaque ventilateur crée deux entités :

- **Ventilateur** — vitesse, sens, mode brise
- **Lumière** — kit LED du plafonnier

Les lampes seules n’ont qu’une entité lumière.

Vous pouvez les ajouter au tableau de bord, aux automatisations et à Alexa/Google si elles passent par Home Assistant.

## Problèmes fréquents

**« Identifiants invalides »**  
Vérifiez e-mail et mot de passe sur l’app Enki. Testez une connexion sur le téléphone avant.

**Aucun appareil détecté**  
L’appareil doit être actif dans l’app Enki (même foyer). Ventilateurs, luminaires, prises Edisio et onduleurs solaires Envertech sont pris en charge.

**Le ventilateur ne réagit pas / erreur dans les journaux**  
Redémarrez Home Assistant après une mise à jour HACS. Vérifiez que la box Enki est en ligne.

**La lumière du ventilo ne correspond pas à l’app**  
Mettez à jour l’intégration via HACS — les corrections d’état lumière sont régulières.

Pour un bug : [ouvrir une issue](https://github.com/cyrilcolinet/enki-integration-hass/issues/new?template=bug.yml) avec la version HA, la version de l’intégration et un extrait des journaux (`enki`).

## Installation manuelle (sans HACS)

1. Téléchargez ce dépôt (ou la dernière [release](https://github.com/cyrilcolinet/enki-integration-hass/releases))
2. Copiez le dossier `custom_components/enki/` dans le dossier `custom_components/` de votre configuration Home Assistant
3. Redémarrez Home Assistant
4. Ajoutez l’intégration comme ci-dessus

## Aide et contribution

| Sujet | Lien |
|-------|------|
| Signaler un bug | [Issues](https://github.com/cyrilcolinet/enki-integration-hass/issues) |
| Demander un appareil | [Feature request](https://github.com/cyrilcolinet/enki-integration-hass/issues/new?template=feature_request.yml) |
| Contribuer au code | [CONTRIBUTING.md](CONTRIBUTING.md) |
| Développement / tests locaux | [docs/DEVELOPMENT.md](docs/DEVELOPMENT.md) |
| Support produit Enki (box, appairage) | [support.enki-home.com](https://support.enki-home.com/) |

## Avertissement

Intégration communautaire, **non affiliée** à Leroy Merlin, Adeo ou Enki. Elle utilise la même API cloud que l’app mobile, qui peut évoluer sans préavis.

Projet dérivé de [CyrilP/hass-enki-component](https://github.com/CyrilP/hass-enki-component).

## Licence

[MIT](LICENSE)
