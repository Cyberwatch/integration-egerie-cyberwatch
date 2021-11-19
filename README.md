# Scripts d'intégration Cyberwatch - Egerie

Scripts réalisés dans le cadre du projet Grand Défi.

## Utilisation

```
pip3 install -r requirements.txt
python3 contextualiser_cyberwatch_avec_egerie.py
```

## Exemple de résultats

```
* Check Cyberwatch API connection...
INFO:root:OK
* Check Egerie API connection...
INFO:OK
* Fetching analyses
! Found XXXX analysis.
* Fetching SupportingAssets from Egerie...
- ... for AnalysisID XXXXXXXXXXX
None
! Found XX supporting assets.
{'XXXXXXX': {'sigma': X, 'environment_id': X}}
* Fetching groups in Cyberwatch...
! Found XX groups.
! Group Application vente en ligne is in EGERIE supporting Assets.
* Affecting criticalities / environments to Cyberwatch assets based on their Egerie SupportingAssets / Cyberwatch groups...
  - Finding criticality / environment to apply to Cyberwatch assets...
  ! Done. Criticality to apply: X
  - Fetching Cyberwatch assets for group_id XXX
    ! Applying criticalities / environments to Cyberwatch assets...
      - Updating DESKTOP-XXXXXXXX...
! Done.
```

## Détails de gestion de projet

Tâche couverte :
- 4.2.2 Permettre à Cyberwatch de récupérer les informations fournies par Egerie afin de contextualiser les actifs scannés par Cyberwatch

Tâche à couvrir (en attente d'APIs complémentaires d'Egerie)
- 4.2.4 Permettre à Cyberwatch d’importer les résultats des analyses financières par actif d'Egerie afin de contextualiser et prioriser les actifs les plus sensibles

Note : les tâches 4.2.1 et 4.2.3 sont couvertes par l'API Cyberwatch documentée sur https://docs.cyberwatch.fr/api/fr/#introduction.

## Licence

Code mis à disposition sous licence MIT.