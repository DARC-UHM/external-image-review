import os
from datetime import datetime

from flask import current_app, jsonify, request, send_file
from mongoengine import DoesNotExist, NotUniqueError
from werkzeug.exceptions import HTTPException

from application.schema.image_reference import ImageReference
from . import image_reference_bp
from .image_reference_saver import ImageReferenceSaver
from .worms_phylogeny_fetcher import WormsPhylogenyFetcher
from ...get_request_ip import get_request_ip
from ...require_api_key import require_api_key


# get all image reference items
@image_reference_bp.get('')
def get_image_references():
    current_app.logger.info(f'Got full image references - IP Address: {get_request_ip()}')
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
        return jsonify({'error': 'Image not found'}), 404


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
    current_app.logger.info("Starting save image reference...")
    image_reference_saver = ImageReferenceSaver(
        tator_url=current_app.config.get("TATOR_URL"),
        image_ref_dir_path=current_app.config.get('IMAGE_REF_DIR_PATH'),
        logger=current_app.logger,
    )
    try:
        if tator_localization_id := request.values.get('tator_localization_id'):
            image_reference_saver.load_from_tator_id(localization_id=tator_localization_id)
        else:
            image_reference_saver.load_from_json(request.get_json())
        saved_ref = image_reference_saver.save()
    except HTTPException as e:
        return jsonify({'error': f'Error loading image reference: {e.description}'}), e.code
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    return jsonify(saved_ref), 201


# refresh an existing image reference with data from Tator
@image_reference_bp.get('/refresh/<image_reference_id>')
@require_api_key
def refresh_image_reference(image_reference_id):
    current_app.logger.info(f'Refresh image reference request for {image_reference_id}')
    try:
        db_record = ImageReference.objects.get(id=image_reference_id)
        current_app.logger.info(f'Scientific name before refresh: {db_record.scientific_name}')
        tator_records = []
        for photo_record in db_record.photo_records:
            saver = ImageReferenceSaver(
                tator_url=current_app.config.get("TATOR_URL"),
                image_ref_dir_path=current_app.config.get('IMAGE_REF_DIR_PATH'),
                logger=current_app.logger,
            )
            saver.load_from_tator_id(elemental_id=photo_record.tator_elemental_id)
            tator_records.append(saver)
        # all photo records must agree on taxonomy, otherwise the refresh should be rejected
        if len({(record.scientific_name, record.tentative_id, record.morphospecies) for record in tator_records}) > 1:
            current_app.logger.error('Conflicting taxonomy in Tator records, cannot refresh image reference')
            return jsonify({'error': 'Photo records have conflicting taxonomy in Tator'}), 409
        first = tator_records[0]
        scientific_name_changed = first.scientific_name != db_record.scientific_name
        try:
            db_record.update(
                set__scientific_name=first.scientific_name,
                set__tentative_id=first.tentative_id,
                set__morphospecies=first.morphospecies,
                set__updated_at=datetime.now(),
            )
        except NotUniqueError:
            current_app.logger.error('Updated taxonomy conflicts with an existing image reference, cannot refresh')
            current_app.logger.error(f'Conflicting taxonomy: scientific_name={first.scientific_name}, '
                                     f'tentative_id={first.tentative_id}, morphospecies={first.morphospecies}')
            return jsonify({'error': 'Updated taxonomy conflicts with an existing image reference'}), 409
        if scientific_name_changed:
            worms_fetcher = WormsPhylogenyFetcher(first.scientific_name)
            worms_fetcher.fetch(current_app.logger)
            phylogeny_updates = {
                f'set__{field}': worms_fetcher.phylogeny.get(field)
                for field in ['phylum', 'class_name', 'order', 'family', 'genus', 'species']
            }
            db_record.update(**phylogeny_updates)
        db_record.reload()
        for db_photo_record, tator_photo_record in zip(db_record.photo_records, tator_records):
            db_photo_record.depth_m = tator_photo_record.depth_m
            db_photo_record.temp_c = tator_photo_record.temp_c
            db_photo_record.salinity_m_l = tator_photo_record.salinity_m_l
            db_photo_record.attracted = True if tator_photo_record.attracted == 'Attracted' else False
        db_record.save()
    except DoesNotExist:
        return jsonify({'error': f'No record found with id {image_reference_id}'}), 404
    except HTTPException as e:
        return jsonify({'error': f'Error refreshing image reference: {e.description}'}), e.code
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    current_app.logger.info(f'Finished refreshing image reference. New scientific name: {db_record.scientific_name}')
    return jsonify(db_record.reload().json()), 200


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
            'error': f'No record found matching request: '
                     f'scientific_name={scientific_name}, '
                     f'morphospecies={request.args.get("morphospecies")}, '
                     f'tentative_id={request.args.get("tentative_id")}'
        }), 404

    return jsonify(db_record.reload().json()), 200


# update a photo record (lat/long, depth, temp, salinity, attracted)
@image_reference_bp.patch('/<scientific_name>/<tator_elemental_id>')
@require_api_key
def update_photo_record(scientific_name, tator_elemental_id):
    try:
        db_record = ImageReference.objects.get(
            scientific_name=scientific_name,
            morphospecies=request.args.get('morphospecies'),
            tentative_id=request.args.get('tentative_id'),
        )
        # find the photo record to update
        photo_record = next((record for record in db_record.photo_records
                             if record.tator_elemental_id == tator_elemental_id), None)
        if not photo_record:
            return jsonify({'error': 'No photo record found matching request'}), 404
        request_json = request.get_json()
        for field in [
            'lat',
            'long',
            'depth_m',
            'temp_c',
            'salinity_m_l',
            'attracted',
        ]:
            if (updated_value := request_json.get(field)) is not None:
                setattr(photo_record, field, updated_value)
        db_record._mark_as_changed('photo_records')
        db_record.save()
    except DoesNotExist:
        return jsonify({
            'error': f'No record found matching request: '
                     f'scientific_name={scientific_name}, '
                     f'morphospecies={request.args.get("morphospecies")}, '
                     f'tentative_id={request.args.get("tentative_id")}'
        }), 404
    return jsonify(db_record.reload().json()), 200


# delete an image reference item
@image_reference_bp.delete('/<scientific_name>')
@require_api_key
def delete_image_reference(scientific_name):
    current_app.logger.info(f'Delete image reference request for {scientific_name}, {request.args.get("morphospecies")},'
                            f' {request.args.get("tentative_id")}')
    try:
        db_record = ImageReference.objects.get(
            scientific_name=scientific_name,
            morphospecies=request.args.get('morphospecies'),
            tentative_id=request.args.get('tentative_id'),
        )
        # delete photos
        for photo_ref in db_record.photo_records:
            for fname in [photo_ref.image_name, photo_ref.thumbnail_name]:
                if fname:
                    fpath = os.path.join(current_app.config.get('IMAGE_REF_DIR_PATH'), fname)
                    if os.path.exists(fpath):
                        current_app.logger.info(f'Deleting file at {fpath}')
                        os.remove(fpath)
                    else:
                        current_app.logger.warning(f'File not found at {fpath}, skipping deletion')
        db_record.delete()
    except DoesNotExist:
        return jsonify({
            'error': f'No record found matching request: '
                     f'scientific_name={scientific_name}, '
                     f'morphospecies={request.args.get("morphospecies")}, '
                     f'tentative_id={request.args.get("tentative_id")}'
        }), 404
    current_app.logger.info('Deleted image reference')
    return jsonify({'message': 'Record deleted'}), 200


# delete a photo record
@image_reference_bp.delete('/<scientific_name>/<tator_elemental_id>')
@require_api_key
def delete_photo_record(scientific_name, tator_elemental_id):
    current_app.logger.info(f'Delete photo record request for  {scientific_name}, {request.args.get("morphospecies")},'
                            f'{request.args.get("tentative_id")}, {tator_elemental_id}')
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
            return jsonify({'error': 'No photo record found matching request'}), 404
        for fname in [record_to_delete.image_name, record_to_delete.thumbnail_name]:
            if fname:
                fpath = os.path.join(current_app.config.get('IMAGE_REF_DIR_PATH'), fname)
                if os.path.exists(fpath):
                    current_app.logger.info(f'Deleting file at {fpath}')
                    os.remove(fpath)
                else:
                    current_app.logger.warning(f'File not found at {fpath}, skipping deletion')
        db_record.update(pull__photo_records=record_to_delete)
    except DoesNotExist:
        return jsonify({
            'error': f'No record found matching request: '
                     f'scientific_name={scientific_name}, '
                     f'morphospecies={request.args.get("morphospecies")}, '
                     f'tentative_id={request.args.get("tentative_id")}'
        }), 404
    current_app.logger.info('Deleted photo record')
    return jsonify({'message': 'Record deleted'}), 200
