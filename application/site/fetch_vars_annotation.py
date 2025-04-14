from json import JSONDecodeError

import requests
from flask import current_app


def fetch_vars_annotation(record_ptr: dict):
    with requests.get(f'{current_app.config.get("HURLSTOR_URL")}:8082/v1/annotations/{record_ptr["uuid"]}') as r:
        try:
            server_record = r.json()
            record_ptr['concept'] = server_record['concept']
        except (JSONDecodeError, KeyError):
            current_app.logger.error(f'Failed to decode JSON for {record_ptr["uuid"]} (reviewer: {record_ptr.get("annotator")})')
            return
        if server_record.get('associations'):  # check for "identity-certainty: maybe" and "identity-reference"
            for association in server_record['associations']:
                if association['link_name'] == 'identity-certainty':
                    record_ptr['id_certainty'] = association['link_value']
                elif association['link_name'] == 'identity-reference':
                    # dive num + id ref to account for duplicate numbers across dives
                    record_ptr['id_reference'] = f'{record_ptr["sequence"][-2:]}:{association["link_value"]}'
                elif association['link_name'] == 'sample-reference':
                    record_ptr['sample_reference'] = association['link_value']
        if server_record.get('ancillary_data'):  # get ctd
            for ancillary_data in server_record['ancillary_data']:
                if ancillary_data == 'latitude':
                    record_ptr['lat'] = server_record['ancillary_data']['latitude']
                elif ancillary_data == 'longitude':
                    record_ptr['long'] = server_record['ancillary_data']['longitude']
                elif ancillary_data == 'depth_meters':
                    record_ptr['depth'] = server_record['ancillary_data']['depth_meters']
                elif ancillary_data == 'temperature_celsius':
                    record_ptr['temperature'] = server_record['ancillary_data']['temperature_celsius']
                elif ancillary_data == 'oxygen_ml_l':
                    record_ptr['oxygen_ml_l'] = server_record['ancillary_data']['oxygen_ml_l']
