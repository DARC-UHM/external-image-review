from flask import current_app, jsonify, request
from mongoengine import DoesNotExist

from schema.image_reference import ImageReference
from . import image_reference_bp
from .worms_phylogeny_fetcher import WormsPhylogenyFetcher
from ...require_api_key import require_api_key


# get all image reference items
@image_reference_bp.get('')
def get_image_references():
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
    image_references = ImageReference.objects(**query_filter)
    return jsonify([
        image_ref.json() for image_ref in image_references
    ]), 200


# create a new image reference item
@image_reference_bp.post('')
@require_api_key
def add_image_reference():
    current_app.logger.info(f'Adding new image reference, request values: {request.values}')
    scientific_name = request.values.get('scientific_name')
    expedition_added = request.values.get('expedition_added')
    tator_id = request.values.get('tator_id')
    if not scientific_name or not expedition_added or not tator_id:
        return jsonify({400: 'Missing required values'}), 400
    if ImageReference.objects(
            scientific_name=scientific_name,
            tentative_id=request.values.get('tentative_id'),
            morphospecies=request.values.get('morphospecies'),
    ):
        return jsonify({409: 'Record already exists'}), 409
    attr = {
        'scientific_name': scientific_name,
        'expedition_added': expedition_added,
        'photo_records': [{
            'tator_id': tator_id,
            'lat': request.values.get('lat'),
            'long': request.values.get('long'),
            'depth_m': request.values.get('depth_m'),
            'temp_c': request.values.get('temp_c'),
            'salinity_m_l': request.values.get('salinity_m_l'),
        }],
    }
    for field in ['tentative_id', 'morphospecies']:
        if field in request.values and request.values.get(field):
            attr[field] = request.values.get(field)
    worms_fetcher = WormsPhylogenyFetcher(scientific_name)
    worms_fetcher.fetch(current_app.logger)
    for field in [
        'phylum',
        'class_name',
        'order',
        'family',
        'genus',
        'species',
    ]:
        if worms_fetcher.phylogeny.get(field):
            attr[field] = worms_fetcher.phylogeny[field]
    image_ref = ImageReference(**attr).save()
    return jsonify(image_ref.json()), 201


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
            'expedition_added',
            'phylum',
            'class_name',
            'order',
            'family',
            'genus',
            'species',
        ]:
            if updated_value := request.values.get(field):
                db_record.update(**{f'set__{field}': updated_value})
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


# add a photo record
@image_reference_bp.post('/<scientific_name>')
@require_api_key
def create_photo_record(scientific_name):
    current_app.logger.info(f'Adding new photo record, request values: {request.values}')
    tator_id = request.values.get('tator_id')
    if not tator_id:
        return jsonify({400: 'Missing required values'}), 400
    try:
        db_record = ImageReference.objects.get(
            scientific_name=scientific_name,
            morphospecies=request.args.get('morphospecies'),
            tentative_id=request.args.get('tentative_id'),
        )
        for record in db_record.photo_records:
            if record.tator_id == int(tator_id):
                return jsonify({409: 'Photo record already exists'}), 409
        if len(db_record.photo_records) >= 5:
            return jsonify({400: 'Can\'t add more than five photo records'}), 400
        db_record.update(push__photo_records={
            'tator_id': tator_id,
            'lat': request.values.get('lat'),
            'long': request.values.get('long'),
            'depth_m': request.values.get('depth_m'),
            'temp_c': request.values.get('temp_c'),
            'salinity_m_l': request.values.get('salinity_m_l'),
        })
    except DoesNotExist:
        return jsonify({
            404: f'No record found matching request: '
                 f'scientific_name={scientific_name}, '
                 f'morphospecies={request.args.get("morphospecies")}, '
                 f'tentative_id={request.args.get("tentative_id")}'
        }), 404
    return jsonify(ImageReference.objects.get(
        scientific_name=scientific_name,
        morphospecies=request.args.get('morphospecies'),
        tentative_id=request.args.get('tentative_id'),
    ).json()), 201


# update a photo record
@image_reference_bp.patch('/<scientific_name>/<tator_id>')
@require_api_key
def update_photo_record(scientific_name, tator_id):
    try:
        db_record = ImageReference.objects.get(
            scientific_name=scientific_name,
            morphospecies=request.args.get('morphospecies'),
            tentative_id=request.args.get('tentative_id'),
        )
        # find the photo record to update
        photo_record = next(
            (record for record in db_record.photo_records if record.tator_id == int(tator_id)), None
        )
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
        db_record.delete()
    except DoesNotExist:
        return jsonify({
            404: f'No record found matching request: '
                 f'scientific_name={scientific_name}, '
                 f'morphospecies={request.args.get("morphospecies")}, '
                 f'tentative_id={request.args.get("tentative_id")}'
        }), 404
    return jsonify({200: 'Record deleted'}), 200
