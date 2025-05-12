import os
from datetime import datetime

from flask import current_app, jsonify, request, send_file
from mongoengine import DoesNotExist
from werkzeug.exceptions import HTTPException

from schema.image_reference import ImageReference
from . import image_reference_bp
from .image_reference_saver import ImageReferenceSaver
from ...require_api_key import require_api_key


# get all image reference items
@image_reference_bp.get('')
def get_image_references():
    current_app.logger.info(f'Got full image references - IP Address: {request.remote_addr}')
    query_filter = {}
    if phylum := request.args.get('phylum'):
        query_filter['phylum'] = phylum
    if class_name := request.args.get('class'):
        query_filter['class_name'] = class_name
    if order := request.args.get('order'):
        query_filter['order'] = order
    if family := request.args.get('family'):
        query_filter['family'] = family
    if genus := request.args.get('genus'):
        query_filter['genus'] = genus
    if species := request.args.get('species'):
        query_filter['species'] = species
    image_references = ImageReference.objects(**query_filter).order_by(
        'phylum',
        'class_name',
        'order',
        'family',
        'genus',
        'species',
        'scientific_name',
        'tentative_id',
    )
    return jsonify([
        image_ref.json() for image_ref in image_references
    ]), 200


# get all references quick version
@image_reference_bp.get('/quick')
def get_image_references_quick():
    ret_dict = {}
    for image_ref in ImageReference.objects():
        ret_dict |= image_ref.json_quick()
    return ret_dict


@image_reference_bp.get('/image/<image_name>')
def get_image(image_name):
    file_path = os.path.join(os.getcwd(), current_app.config.get('IMAGE_REF_DIR_PATH'), image_name)
    if os.path.exists(file_path):
        return send_file(file_path)
    else:
        return jsonify({404: 'Image not found'}), 404


@image_reference_bp.post('')
@require_api_key
def add_image_reference():
    """
    Create a new image reference item with one photo record or update an existing one.
    curl -X POST http://localhost:5000/image-reference \
      -d '{
            "scientific_name="Some Name",
            "morphospecies": "morphospecies (optional)",
            "tentative_id": "tentative id (optional)",
            "deployment_name": "PNG_123",
            "section_id": 12345,
            "tator_elemental_id": 12345,
            "localization_media_id": 123,
            "localization_frame": 123,
            "localization_type": 48,
            "normalized_top_left_x_y": [0.1, 0.2],
            "normalized_dimensions": [0.3, 0.4]
          }'
    """
    image_reference_saver = ImageReferenceSaver(
        tator_url=current_app.config.get("TATOR_URL"),
        image_ref_dir_path=current_app.config.get('IMAGE_REF_DIR_PATH'),
        logger=current_app.logger,
    )
    try:
        if tator_elemental_id := request.values.get('tator_elemental_id'):
            image_reference_saver.load_from_tator_elemental_id(tator_elemental_id)
        else:
            image_reference_saver.load_from_json(request.get_json())
        saved_ref = image_reference_saver.save()
    except HTTPException as e:
        return jsonify({e.code: f'Error loading image reference: {e.description}'}), e.code
    except ValueError as e:
        return jsonify({400: 'Missing required values'}), 400
    return jsonify(saved_ref), 201


# update an existing image reference item
@image_reference_bp.patch('/<scientific_name>')
@require_api_key
def update_image_reference(scientific_name):
    # query params are the current record values, body params are the new values
    try:
        # this is how unique records are identified
        db_record = ImageReference.objects.get(
            scientific_name=scientific_name,
            morphospecies=request.args.get('morphospecies'),
            tentative_id=request.args.get('tentative_id'),
        )
        for field in [
            'morphospecies',
            'tentative_id',
            'phylum',
            'class_name',
            'order',
            'family',
            'genus',
            'species',
        ]:
            if updated_value := request.values.get(field):
                db_record.update(**{f'set__{field}': updated_value})
            db_record.update(**{f'set__updated_at': datetime.now()})
    except DoesNotExist:
        return jsonify({
            404: f'No record found matching request: '
                 f'scientific_name={scientific_name}, '
                 f'morphospecies={request.args.get("morphospecies")}, '
                 f'tentative_id={request.args.get("tentative_id")}'
        }), 404

    return jsonify(ImageReference.objects.get(
        scientific_name=scientific_name,
        morphospecies=request.values.get('morphospecies') or request.args.get('morphospecies'),
        tentative_id=request.values.get('tentative_id') or request.args.get('tentative_id'),
    ).json()), 200


# update a photo record (lat/long, depth, temp, salinity)
@image_reference_bp.patch('/<scientific_name>')
@require_api_key
def update_photo_record(scientific_name):
    tator_elemental_id = request.args.get('tator_elemental_id')
    try:
        db_record = ImageReference.objects.get(
            scientific_name=scientific_name,
            morphospecies=request.args.get('morphospecies'),
            tentative_id=request.args.get('tentative_id'),
        )
        # find the photo record to update
        photo_record = next((record for record in db_record.photo_records
                             if record.tator_id == tator_elemental_id), None)
        for field in [
            'lat',
            'long',
            'depth_m',
            'temp_c',
            'salinity_m_l',
        ]:
            if updated_value := request.values.get(field):
                photo_record.update(**{f'set__{field}': updated_value})
    except DoesNotExist:
        return jsonify({
            404: f'No record found matching request: '
                 f'scientific_name={scientific_name}, '
                 f'morphospecies={request.args.get("morphospecies")}, '
                 f'tentative_id={request.args.get("tentative_id")}'
        }), 404
    return jsonify(ImageReference.objects.get(
        scientific_name=scientific_name,
        morphospecies=request.values.get('morphospecies') or request.args.get('morphospecies'),
        tentative_id=request.values.get('tentative_id') or request.args.get('tentative_id'),
    ).json()), 200


# delete an image reference item
@image_reference_bp.delete('/<scientific_name>')
@require_api_key
def delete_image_reference(scientific_name):
    try:
        db_record = ImageReference.objects.get(
            scientific_name=scientific_name,
            morphospecies=request.args.get('morphospecies'),
            tentative_id=request.args.get('tentative_id'),
        )
        # delete photos
        for photo_ref in db_record.photo_records:
            if photo_ref.image_name:
                os.remove(os.path.join(current_app.config.get('IMAGE_REF_DIR_PATH'), photo_ref.image_name))
            if photo_ref.thumbnail_name:
                os.remove(os.path.join(current_app.config.get('IMAGE_REF_DIR_PATH'), photo_ref.thumbnail_name))
        db_record.delete()
    except DoesNotExist:
        return jsonify({
            404: f'No record found matching request: '
                 f'scientific_name={scientific_name}, '
                 f'morphospecies={request.args.get("morphospecies")}, '
                 f'tentative_id={request.args.get("tentative_id")}'
        }), 404
    return jsonify({200: 'Record deleted'}), 200


# delete a photo record
@image_reference_bp.delete('/<scientific_name>/<tator_elemental_id>')
@require_api_key
def delete_photo_record(scientific_name, tator_elemental_id):
    try:
        db_record = ImageReference.objects.get(
            scientific_name=scientific_name,
            morphospecies=request.args.get('morphospecies'),
            tentative_id=request.args.get('tentative_id'),
        )
        # delete photos
        record_to_delete = next((record for record in db_record.photo_records
                                 if record.tator_elemental_id == tator_elemental_id), None)
        if not record_to_delete:
            return jsonify({404: 'No photo record found matching request'}), 404
        if record_to_delete.image_name:
            os.remove(os.path.join(current_app.config.get('IMAGE_REF_DIR_PATH'), record_to_delete.image_name))
        if record_to_delete.thumbnail_name:
            os.remove(os.path.join(current_app.config.get('IMAGE_REF_DIR_PATH'), record_to_delete.thumbnail_name))
        db_record.update(pull__photo_records=record_to_delete)
    except DoesNotExist:
        return jsonify({
            404: f'No record found matching request: '
                 f'scientific_name={scientific_name}, '
                 f'morphospecies={request.args.get("morphospecies")}, '
                 f'tentative_id={request.args.get("tentative_id")}'
        }), 404
    return jsonify({200: 'Record deleted'}), 200
