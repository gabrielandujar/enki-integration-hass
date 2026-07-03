# Clés gateway volets — guide contributeur

Ce document s’adresse aux **personnes à l’aise avec le réseau / le débogage mobile**. Les testeurs lambda n’ont pas besoin de le lire : voir [Beta volets — pour les testeurs](SUPPORTED_DEVICES.md#pour-les-testeurs) dans `SUPPORTED_DEVICES.md`.

## État actuel

Pour les **volets** (`api-enki-rolling-prod`, APK ≥ 2.25.1), la clé **`ENKI_ACCESS_MOTORIZATION_API_KEY`** est déjà incluse dans `const.py` (extraite de l’APK Enki 2.25.1). L’ancien micro-service `api-enki-access-and-motorizations-prod` n’est plus utilisé.

Les utilisateurs **n’ont rien à configurer** : l’entité **« Volet (beta) »** apparaît si le volet est actif dans l’app Enki et que l’intégration est en **v1.5.0+**.

## Quand relire ce guide

- **Mise à jour de l’app Enki** — les clés gateway peuvent changer ; la méthode recommandée est `scripts/extract_gateway_keys.py` (voir [DEVELOPMENT.md](DEVELOPMENT.md)).
- **HTTP 403** sur `api-enki-rolling-prod` — valider la clé embarquée vs le trafic réel de l’app (mitmproxy ci-dessous).
- **Échec de l’extraction APK** — capturer manuellement `X-Gateway-APIKey` et ouvrir une issue ou PR.

**Ce n’est pas :**

- le mot de passe du compte Enki ;
- un secret personnel lié à un foyer ;
- une donnée à partager publiquement sur les réseaux sociaux (c’est une clé applicative Leroy Merlin / Adeo, réutilisable pour toute l’intégration une fois intégrée au repo).

## Ce qu’il faut récupérer (validation manuelle)

Lors d’un contrôle de volet dans l’app Enki, repérer une requête HTTP vers :

```text
…/api-enki-rolling-prod/v1/shutter/{nodeId}/…
```

Copier la valeur de l’en-tête :

```text
X-Gateway-APIKey: <valeur à comparer ou transmettre au mainteneur>
```

Actions typiques visibles dans l’URL : `check-shutter-position`, `change-shutter-position`, `check-shutter-opening`.

## Méthode recommandée — extraction APK

Sur la machine de dev :

```bash
python3 scripts/extract_gateway_keys.py chemin/vers/enki.apk --apply --update-known
```

Le script met à jour `custom_components/enki/const.py` (dont `ENKI_ACCESS_MOTORIZATION_API_KEY`). Détail : [DEVELOPMENT.md](DEVELOPMENT.md).

## Alternative — mitmproxy (validation réseau)

### Prérequis

- PC et téléphone sur le **même réseau Wi‑Fi**
- [mitmproxy](https://mitmproxy.org/) installé sur le PC
- App **Enki** sur le téléphone, avec au moins un volet fonctionnel

### Étapes

1. **Lancer mitmproxy** sur le PC :
   ```bash
   mitmweb
   ```
   Interface web : http://127.0.0.1:8081 — proxy écoute sur le port **8080**.

2. **Configurer le proxy Wi‑Fi sur le téléphone**  
   Réglages Wi‑Fi → réseau actuel → proxy manuel → IP du PC, port **8080**.

3. **Installer le certificat mitmproxy** sur le téléphone  
   Sur le téléphone, ouvrir http://mitm.it et suivre les instructions (iOS ou Android). Sans certificat, le trafic HTTPS de l’app ne sera pas visible.

4. **Contrôler un volet dans l’app Enki**  
   Ouvrir, fermer ou régler la position d’un volet.

5. **Filtrer le trafic** dans mitmweb  
   Rechercher `rolling-prod` ou `change-shutter`.

6. **Copier `X-Gateway-APIKey`** depuis les en-têtes de la requête et la comparer à `ENKI_ACCESS_MOTORIZATION_API_KEY` dans `const.py`.

7. **Désactiver le proxy** sur le téléphone une fois terminé.

### Transmission au projet

Si la clé diffère de celle du dépôt, ouvrir une [issue](https://github.com/cyrilcolinet/enki-integration-hass/issues/new) ou commenter sur une issue volets existante avec :

- la valeur de `X-Gateway-APIKey` (texte seul) ;
- modèle de volet testé (ex. Evology SIN2RS1) ;
- version de l’app Enki (APK) ;
- confirmation que la commande fonctionnait dans l’app au moment de la capture.

**Ne jamais joindre :** e-mail, mot de passe, tokens Bearer, homeId, nodeId.

## Alternative — HTTP Toolkit

[HTTP Toolkit](https://httptoolkit.com/) propose une interface graphique (connexion téléphone Android via ADB, ou proxy manuel similaire à mitmproxy). Même principe : intercepter une requête `api-enki-rolling-prod` / `shutter/…` et lire `X-Gateway-APIKey`.

## Intégration côté repo

1. **Préféré :** `extract_gateway_keys.py --apply --update-known` (voir ci-dessus).
2. **Sinon :** le mainteneur met à jour manuellement :

```python
# custom_components/enki/const.py
ENKI_ACCESS_MOTORIZATION_API_KEY = "…"
```

Puis publie une nouvelle version. Les utilisateurs n’ont rien à modifier manuellement s’ils passent par HACS.

## Références

- Notes API volets : [API.md](API.md#roller-shutters-evology-sin2rs1--beta)
- Testeurs (sans proxy) : [SUPPORTED_DEVICES.md](SUPPORTED_DEVICES.md#pour-les-testeurs)
