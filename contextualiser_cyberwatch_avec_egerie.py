######################################################################################################################################################
# CONTEXTUALISATION DES ANALYSES CYBERWATCH SUR LA BASE DES DONNEES D'EGERIE
# Ce script effectue les travaux suivants :
# 1. Récupérer les "SupportingAssets" d'EGERIE
# 2. Récupérer les labels de chaque SupportingAsset, ainsi que leurs impact_sigma_score_maj (valeur bornée de 0.00 à 1.00)
# 3. Récupérer les groupes de CYBERWATCH
# 4. Pour chaque groupe figurant dans la liste des SupportingAssets d'EGERIE, récupérer les actifs correspondants
# 5. Pour chaque actif ainsi obtenu :
#      - appliquer une stratégie de priorisation Elevée si l'actif a un impact_sigma_score_maj >= 0.66
#      - appliquer une stratégie de priorisation Moyenne si l'actif a un impact_sigma_score_maj >= 0.33 et < 0.66
#      - appliquer une stratégie de priorisation Basse si l'actif a un impact_sigma_score_maj < 0.33.
# Les actions définies au point 5 sont paramétrable, afin de définir des seuils différents et des stratégies différentes sur les besoins des clients.
######################################################################################################################################################
# Auteur : Maxime ALAY-EDDINE (Cyberwatch SAS)
# Licence : MIT


import os
import requests
import json
from configparser import ConfigParser
from cbw_api_toolbox.cbw_api import CBWApi

####################################################################################
# EGERIE / CYBERWATCH SETTINGS
# Cette section peut être modifiée par l'utilisateur pour l'adapter à ses besoins
#
####################################################################################
# ANALYSES EGERIE
# Laisser à [] pour récupérer toutes les analyses // Leave to [] to fetch all analysis
# Sinon, mettre une liste d'ID au format string.
# TODO: EGERIE permettra au T2 2022 de récupérer la liste de toutes les analyses par API
# En attendant, il faut absolument mettre au moins une valeur.
# Pour récupérer cette valeur, aller sur Gestion des risques > Modules, sélectionner un module,
# et identifier le numéro de l'analyse dans la barre d'adresse du navigateur web.
# Le format est https://<HOST_EGERIE>/EgerieRM/Module/<ANALYSIS_ID>/Accueil et il faut prendre le ANALYSIS_ID
EGERIE_ANALYSIS_TO_FETCH = [
    # <Insérer les analyses ID ici>
]

# ENVIRONNEMENTS METIERS A AFFECTER DANS CYBERWATCH
# Mettre un tableau de dict au format {'sigma_min': X, 'sigma_max': Y, 'environment_id': N}
# La criticité d'ID N sera appliquée aux actifs dont les groupes sont dans sigma_min <= SIGMA <= sigma_max
# Par défaut, nous mettons une criticité basse pour sigma entre 0 et 0.33, moyenne entre 0.33 et 0.66, et élevée pour 0.66 à 1.
CYBERWATCH_ENVIRONMENTS_TO_APPLY = [
    {
        'sigma_min': 0.0,
        'sigma_max': 0.33,
        'environment_id': 1
    },
    {
        'sigma_min': 0.33,
        'sigma_max': 0.66,
        'environment_id': 2
    },
        {
        'sigma_min': 0.66,
        'sigma_max': 1.0,
        'environment_id': 3
    }
]

#=========================================================================================
# MAIN CODE
#=========================================================================================

CONF = ConfigParser()
CONF.read(os.path.join(os.path.abspath(os.path.dirname(__file__)), '.', 'api.conf'))
CBW_CLIENT = CBWApi(CONF.get('cyberwatch', 'url'), CONF.get('cyberwatch', 'api_key'), CONF.get('cyberwatch', 'secret_key'))
EGERIE_API_BASENAME = CONF.get('egerie', 'server_name')
EGERIE_AUTH = {
    '_username': CONF.get('egerie', 'username'),
    '_password': CONF.get('egerie', 'password')
}

##############################
# AUTH / CONNECTIVITY CHECK
##############################

def egerie_connect():
    e_auth_request = requests.post(EGERIE_API_BASENAME+'/v4/login_check', json=EGERIE_AUTH)
    if e_auth_request.status_code == 200:
        token = e_auth_request.json()['token']
        return token
    else:
        return

print('* Check Cyberwatch API connection...')
CBW_CLIENT.ping()
print('* Check Egerie API connection...')
token = egerie_connect()
if token:
    print('INFO:OK')
else:
    print('ERROR: Please check the Egerie API credentials.')

EGERIE_AUTH_HEADERS = {
    'X-Security-Token': 'Bearer '+token
}

#############################
# RECUPERATION DES ANALYSES
#############################

print('* Fetching analyses')
if len(EGERIE_ANALYSIS_TO_FETCH) == 0:
    print('! WARNING: EGERIE will provide the feature to list all analysis only on Q2 2022. In the meantime, please provide a valid Analysis ID by hand.')
    print('! ERROR: Please provide at least one Analysis_ID. Check the code comment or please contact our support to do so.')
    exit(1)
print('! Found '+str(len(EGERIE_ANALYSIS_TO_FETCH))+' analysis.')

###################################
# RECUPERATION DES BIENS SUPPORTS
###################################

print('* Fetching SupportingAssets from Egerie...')
supporting_assets = {}
for analysis in EGERIE_ANALYSIS_TO_FETCH:
    analysis = str(analysis)
    print('- ... for AnalysisID '+analysis)
    e_supporting_assets = requests.get(EGERIE_API_BASENAME+'/v4/EgerieRM/api/analyses/'+analysis+'/supporting-assets?iss=1', headers=EGERIE_AUTH_HEADERS)
    print(e_supporting_assets.encoding)
    res = e_supporting_assets.json()['data']
    print('! Found '+str(len(res))+' supporting assets.')
    for r in res:
        if not(r['data']['label'] in supporting_assets.keys()):
            supporting_assets[r['data']['label']] = {}
        supporting_assets[r['data']['label']]['sigma'] = r['data']['impact_sigma_score_maj']
        for cbw_environment in CYBERWATCH_ENVIRONMENTS_TO_APPLY:
            if ((supporting_assets[r['data']['label']]['sigma'] >= cbw_environment['sigma_min']) and (supporting_assets[r['data']['label']]['sigma'] <= cbw_environment['sigma_max'])):
                supporting_assets[r['data']['label']]['environment_id'] = cbw_environment['environment_id']
print(supporting_assets)

#######################################
# RECUPERATION DES GROUPES CYBERWATCH
#######################################

print('* Fetching groups in Cyberwatch...')
groups = CBW_CLIENT.groups()
print('! Found '+str(len(groups))+' groups.')
for g in groups:
    if g.name in supporting_assets.keys():
        print('! Group '+g.name+' is in EGERIE supporting Assets.')
        supporting_assets[g.name]['cbw_group_id'] = g.id
    #else:
        #print ('  Skipping '+g.name+' as it is not a SupportingAsset.')

###############################
# AFFECTATION DES CRITICITES
###############################

print('* Affecting criticalities / environments to Cyberwatch assets based on their Egerie SupportingAssets / Cyberwatch groups...')
for sa in supporting_assets.keys():
    # We skip if the SupportingAsset has no Cyberwatch equivalent group
    if not('cbw_group_id' in supporting_assets[sa].keys()):
        continue
    # Otherwise we apply the appropriate criticality to the asset
    print('  - Finding criticality / environment to apply to Cyberwatch assets...')
    print('  ! Done. Criticality to apply: '+str(supporting_assets[sa]['environment_id']))
    print('  - Fetching Cyberwatch assets for group_id '+str(supporting_assets[sa]['cbw_group_id']))
    cbw_assets = CBW_CLIENT.servers({'group_id': supporting_assets[sa]['cbw_group_id']})
    print('    ! Applying criticalities / environments to Cyberwatch assets...')
    for cbw_a in cbw_assets:
        print('      - Updating '+str(cbw_a.hostname)+'...')
        CBW_CLIENT.update_server(str(cbw_a.id), {'environment': str(supporting_assets[sa]['environment_id'])})
print('! Done.')
