import logging
import os

import requests
from mongoengine import DoesNotExist

from schema.comment import Comment
from schema.dropcam_field_book import DropcamFieldBook


def fetch_tator_localizations(
        elemental_ids: list,
        tator_localizations: dict,
        url_root: str,
        tator_url: str,
        logger: logging.Logger,
):
    deleted_localizations = []
    res = requests.put(
        url=f'{tator_url}/rest/Localizations/26?show_deleted=1',
        headers={
            'Authorization': f'Token {os.environ.get("TATOR_TOKEN")}',
            'Content-Type': 'application/json',
            'accept': 'application/json',
        },
        json={
            "object_search": {
                "attribute": "$elemental_id",
                "operation": "in",
                "value": elemental_ids,
            },
        },
    )
    if res.status_code != 200:
        logger.error(f'Failed to fetch Tator localizations for one of {elemental_ids})')
        return
    updated_localizations = res.json()
    expeditions = {}
    for updated_localization in updated_localizations:
        uuid = updated_localization['elemental_id']
        if updated_localization.get('variant_deleted'):
            deleted_localizations.append(uuid)
        else:
            update_localization_in_dict(
                tator_localizations[uuid],
                updated_localization,
                expeditions,
                url_root,
            )
    for uuid in deleted_localizations:
        logger.info(f'Tator reports that localization {uuid} has been deleted, removing from the database')
        del tator_localizations[uuid]  # remove from dict
        try:  # remove from database
            db_record = Comment.objects.get(uuid=uuid)
            db_record.delete()
        except DoesNotExist:
            logger.error(f'Failed to delete comment with uuid {uuid} from the database')
            continue


def update_localization_in_dict(localization: dict, updated_localization: dict, expeditions: dict, url_root: str):
    localization['concept'] = f'{updated_localization["attributes"]["Scientific Name"]}'
    if updated_localization['attributes']['Tentative ID'] != '':
        localization['concept'] += f' ({updated_localization["attributes"]["Tentative ID"]}?)'
    elif updated_localization['attributes'].get('Morphospecies') and updated_localization['attributes']['Morphospecies'] != '':
        localization['concept'] += f' ({updated_localization["attributes"]["Morphospecies"]})'
    localization['id_certainty'] = updated_localization['attributes'].get('IdentificationRemarks')
    localization['image_url'] = \
        f'{url_root}tator-frame/{updated_localization["media"]}/{updated_localization["frame"]}?preview=true'
    localization['depth'] = updated_localization['attributes'].get('Depth')
    localization['temperature'] = updated_localization['attributes'].get('DO Temperature (celsius)')
    localization['oxygen_ml_l'] = updated_localization['attributes'].get('DO Concentration Salin Comp (mol per L)')
    localization['id_reference'] = f'{updated_localization["media"]}:{localization["concept"]}'
    section_id = localization['section_id']
    if section_id not in expeditions.keys():
        try:
            expeditions[section_id] = DropcamFieldBook.objects.get(section_id=section_id).json()
        except DoesNotExist:
            print(f'No expedition found with section ID {section_id}')
            return
    # find deployment with matching sequence
    deployment = next(
        (x for x in expeditions[section_id]['deployments'] if x['deployment_name'] == localization['sequence']),
        None,
    )
    if deployment is None:
        return
    localization['expedition_name'] = expeditions[section_id]['expedition_name']
    localization['lat'] = deployment['lat']
    localization['long'] = deployment['long']
    localization['bait_type'] = deployment['bait_type']
    if localization.get('depth') is None:
        localization['depth'] = deployment.get('depth_m')
