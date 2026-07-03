# Appareils et fonctionnalités supportés

Détail par type d’appareil et entités Home Assistant créées. L’intégration détecte les appareils via leurs **capabilities** API (comme l’app mobile), pas seulement par modèle.

Version de référence : **1.2.0**

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

## Prises et interrupteurs (Edisio, …)

**Entité HA :** lumière ON/OFF (API power Enki)

| Fonction | Détail |
|----------|--------|
| Marche / arrêt | Via `switch-electrical-power` |

Les nœuds multi-circuits peuvent créer **une entité par circuit** (endpoint BFF).

## Panneaux solaires (Envertech-Lexman)

**Entité HA :** capteur de production (W)

| Fonction | Détail |
|----------|--------|
| Production instantanée | Valeur lue sur le dashboard BFF |

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
| Bientôt | Radiateurs ACOVA ARLAN |
| Non planifié | Alarme Enki (pas d’API identifiée) |
| Hors périmètre | Box Enki, appairage, compte Leroy Merlin → [support Enki](https://support.enki-home.com/) |

Documentation API : [API.md](API.md)
