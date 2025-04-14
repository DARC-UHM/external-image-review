from json import JSONDecodeError

from flask import jsonify, current_app, request
from mongoengine import DoesNotExist, NotUniqueError

from schema.dropcam_field_book import DropcamFieldBook
from . import dropcam_fieldbook_bp
from ...require_api_key import require_api_key


# get dropcam fieldbook by section id
@dropcam_fieldbook_bp.get('/dropcam-fieldbook/<section_id>')
@require_api_key
def get_dropcam_field_book(section_id):
    try:
        return jsonify(DropcamFieldBook.objects.get(section_id=section_id).json()), 200
    except DoesNotExist:
        return jsonify({404: 'No record matching given section id'}), 404


# create new dropcam fieldbook
@dropcam_fieldbook_bp.post('/dropcam-fieldbook')
@require_api_key
def add_dropcam_field_book():
    current_app.logger.info(f'Updating dropcam fieldbook...')
    try:
        expedition_fieldbook = request.json
        field_book = DropcamFieldBook(
            section_id=expedition_fieldbook['section_id'],
            expedition_name=expedition_fieldbook['expedition_name'],
            deployments=[
                {
                    'deployment_name': deployment['deployment_name'],
                    'lat': deployment['lat'],
                    'long': deployment['long'],
                    'depth_m': deployment.get('depth_m'),
                    'bait_type': deployment['bait_type'],
                }
                for deployment in expedition_fieldbook['deployments']
            ]
        ).save()
    except JSONDecodeError:
        current_app.logger.info(f'Invalid JSON')
        return jsonify({400: 'Invalid JSON'}), 400
    except KeyError:
        current_app.logger.info(f'Missing required values')
        return jsonify({400: 'Missing required values'}), 400
    except NotUniqueError:
        # delete current record and replace with new one
        expedition_fieldbook = request.json
        DropcamFieldBook.objects.get(section_id=expedition_fieldbook['section_id']).delete()
        field_book = DropcamFieldBook(
            section_id=expedition_fieldbook['section_id'],
            expedition_name=expedition_fieldbook['expedition_name'],
            deployments=[
                {
                    'deployment_name': deployment['deployment_name'],
                    'lat': deployment['lat'],
                    'long': deployment['long'],
                    'depth_m': deployment.get('depth_m'),
                    'bait_type': deployment['bait_type'],
                }
                for deployment in expedition_fieldbook['deployments']
            ]
        ).save()
        current_app.logger.info(f'Fieldbook updated for section ID: {expedition_fieldbook["section_id"]}')
        return jsonify(field_book.json()), 200
    current_app.logger.info(f'Fieldbook created for section ID: {expedition_fieldbook["section_id"]}')
    return jsonify(field_book.json()), 201
