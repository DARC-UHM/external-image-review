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
    photo_url = request.values.get('photo_url')
    if not scientific_name or not expedition_added or not photo_url:
        return jsonify({400: 'Missing required values'}), 400
    attr = {
        'scientific_name': scientific_name,
        'expedition_added': expedition_added,
        'photos': [photo_url],
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
    if ImageReference.objects(scientific_name=scientific_name):
        return jsonify({409: 'Record already exists'}), 409
    image_ref = ImageReference(**attr).save()
    return jsonify(image_ref.json()), 201


# update an existing image reference item
@image_reference_bp.patch('/<scientific_name>')
@require_api_key
def update_image_reference(scientific_name):
    morphospecies = request.values.get('morphospecies')
    tentative_id = request.values.get('tentative_id')
    photos = request.values.getlist('photos')
    if not morphospecies and not tentative_id and not photos:
        return jsonify({400: 'Missing required values'}), 400
    try:
        db_record = ImageReference.objects.get(scientific_name=scientific_name)
        if morphospecies:
            db_record.update(set__morphospecies=morphospecies)
        if tentative_id:
            db_record.update(set__tentative_id=tentative_id)
        if photos:
            db_record.update(set__photos=photos)
    except DoesNotExist:
        return jsonify({404: 'No record with given scientific name'}), 404
    return jsonify(ImageReference.objects.get(scientific_name=scientific_name).json()), 200


# delete an image reference item
@image_reference_bp.delete('/<scientific_name>')
@require_api_key
def delete_image_reference(scientific_name):
    try:
        db_record = ImageReference.objects.get(scientific_name=scientific_name)
        db_record.delete()
    except DoesNotExist:
        return jsonify({404: 'No record with given scientific name'}), 404
    return jsonify({200: 'Record deleted'}), 200
