import os
from datetime import datetime
from http.client import HTTPException

from flask import current_app, jsonify, request, send_file
from mongoengine import DoesNotExist

from schema.dropcam_field_book import DropcamFieldBook
from schema.image_reference import ImageReference
from . import image_reference_bp
from .tator_data_fetcher import TatorDataFetcher
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


@image_reference_bp.get('/image/<image_name>')
def get_image(image_name):
    file_path = os.path.join(os.getcwd(), current_app.config.get('IMAGE_REF_FOLDER'), image_name)
    if os.path.exists(file_path):
        return send_file(file_path)
    else:
        return jsonify({404: 'Image not found'}), 404


@image_reference_bp.post('')
@require_api_key
def add_image_reference():
    """
    Create a new image reference item with one photo record.
    curl -X POST http://localhost:5000/image-reference \
      -d scientific_name="Some Name" \
      -d morphospecies="optional" \
      -d tentative_id="optional" \
      -d deployment_name="required" \
      -d section_id="required" \
      -d tator_id=12345
    """
    scientific_name = request.values.get('scientific_name')
    tator_id = request.values.get('tator_id')
    tentative_id = request.values.get('tentative_id')
    morphospecies = request.values.get('morphospecies')
    deployment_name = request.values.get('deployment_name')
    section_id = request.values.get('section_id')
    if not scientific_name or not section_id or not deployment_name or not tator_id:
        return jsonify({400: 'Missing required values'}), 400
    if ImageReference.objects(
        scientific_name=scientific_name,
        tentative_id=tentative_id,
        morphospecies=morphospecies,
    ):
        return jsonify({409: 'Record already exists'}), 409
    current_app.logger.info(f'Adding new image reference: scientific_name={scientific_name}, '
                            f'morphospecies={morphospecies}, tentative_id={tentative_id}')
    try:
        fetched_data = fetch_data_and_save_image(tator_id, section_id, deployment_name)
    except HTTPException:
        return jsonify({400: 'Error fetching data from Tator'}), 400
    worms_fetcher = WormsPhylogenyFetcher(scientific_name)
    worms_fetcher.fetch(current_app.logger)
    attr = {
        'scientific_name': scientific_name,
        'photo_records': [{
            'tator_id': tator_id,
            'image_name': fetched_data['image_name'],
            'thumbnail_name': fetched_data['thumbnail_name'],
            'deployment_name': deployment_name,
            'lat': fetched_data['lat'],
            'long': fetched_data['long'],
            'depth_m': fetched_data.get('depth_m'),
            'temp_c': fetched_data.get('temp_c'),
            'salinity_m_l': fetched_data.get('salinity_m_l'),
        }],
    }
    for field in ['tentative_id', 'morphospecies']:
        if field in request.values and request.values.get(field):
            attr[field] = request.values.get(field)
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


# add a photo record
@image_reference_bp.post('/<scientific_name>')
@require_api_key
def create_photo_record(scientific_name):
    tator_id = request.values.get('tator_id')
    deployment_name = request.values.get('deployment_name')
    section_id = request.values.get('section_id')
    morphospecies = request.args.get('morphospecies')
    tentative_id = request.args.get('tentative_id')
    if not tator_id or not deployment_name or not section_id:
        return jsonify({400: 'Missing required values'}), 400
    current_app.logger.info(f'Adding new image reference: scientific_name={scientific_name}, '
                            f'morphospecies={morphospecies}, tentative_id={tentative_id}')
    try:
        db_record = ImageReference.objects.get(
            scientific_name=scientific_name,
            morphospecies=morphospecies,
            tentative_id=tentative_id,
        )
        for record in db_record.photo_records:
            if record.tator_id == int(tator_id):
                return jsonify({409: 'Photo record already exists'}), 409
        if len(db_record.photo_records) >= 5:
            return jsonify({400: 'Can\'t add more than five photo records'}), 400
        fetched_data = fetch_data_and_save_image(tator_id, section_id, deployment_name)
        db_record.update(push__photo_records={
            'tator_id': tator_id,
            'image_name': fetched_data['image_name'],
            'thumbnail_name': fetched_data['thumbnail_name'],
            'deployment_name': deployment_name,
            'lat': fetched_data['lat'],
            'long': fetched_data['long'],
            'depth_m': fetched_data.get('depth_m'),
            'temp_c': fetched_data.get('temp_c'),
            'salinity_m_l': fetched_data.get('salinity_m_l'),
        })
    except HTTPException:
        return jsonify({400: 'Error fetching data from Tator'}), 400
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


def fetch_data_and_save_image(tator_id: str, section_id: str, deployment_name: str) -> dict:
    # get the lat/long from the field book
    dropcam_fieldbook = DropcamFieldBook.objects.get(section_id=section_id)
    if not dropcam_fieldbook:
        current_app.logger.warning(f'No field book found for section {section_id}')
    lat = None
    long = None
    for deployment in dropcam_fieldbook['deployments']:
        if deployment['deployment_name'] == deployment_name:
            lat = deployment['lat']
            long = deployment['long']
            break
    if not lat or not long:
        current_app.logger.warning(f'No lat/long found for deployment {deployment_name}')
    # get the image/ctd data from Tator
    tator_fetcher = TatorDataFetcher(
        localization_id=tator_id,
        tator_url=current_app.config.get('TATOR_URL'),
        logger=current_app.logger,
    )
    tator_fetcher.fetch_localization()
    tator_fetcher.fetch_frame()
    tator_fetcher.save_images(current_app.config.get('IMAGE_REF_FOLDER'))
    return {
        **tator_fetcher.ctd_data,
        'image_name': tator_fetcher.image_name,
        'thumbnail_name': tator_fetcher.thumbnail_name,
        'lat': lat,
        'long': long,
    }


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


# delete a photo record
@image_reference_bp.delete('/<scientific_name>/<tator_id>')
@require_api_key
def delete_photo_record(scientific_name, tator_id):
    try:
        db_record = ImageReference.objects.get(
            scientific_name=scientific_name,
            morphospecies=request.args.get('morphospecies'),
            tentative_id=request.args.get('tentative_id'),
        )
        db_record.update(pull__photo_records__tator_id=int(tator_id))
    except DoesNotExist:
        return jsonify({
            404: f'No record found matching request: '
                 f'scientific_name={scientific_name}, '
                 f'morphospecies={request.args.get("morphospecies")}, '
                 f'tentative_id={request.args.get("tentative_id")}'
        }), 404
    return jsonify({200: 'Record deleted'}), 200
