from flask import jsonify, request
from mongoengine import DoesNotExist

from schema.attracted import Attracted
from . import attracted_bp
from ...require_api_key import require_api_key


# get all attracted items
@attracted_bp.get('')
def get_attracted():
    return jsonify({
        attracted.scientific_name: attracted.attracted for attracted in Attracted.objects()
    }), 200


# create a new attracted item
@attracted_bp.post('')
@require_api_key
def add_attracted():
    scientific_name = request.values.get('scientific_name')
    attracted = request.values.get('attracted')
    if not scientific_name or not attracted:
        return jsonify({400: 'Missing required values'}), 400
    if Attracted.objects(scientific_name=scientific_name):
        return jsonify({409: 'Record already exists'}), 409
    attr = Attracted(scientific_name=scientific_name, attracted=attracted).save()
    return jsonify(attr.json()), 201


# update an existing attracted item
@attracted_bp.patch('/<scientific_name>')
@require_api_key
def update_attracted(scientific_name):
    attracted = request.values.get('attracted')
    if not scientific_name or not attracted:
        return jsonify({400: 'Missing required values'}), 400
    try:
        db_record = Attracted.objects.get(scientific_name=scientific_name)
        db_record.update(set__attracted=attracted)
    except DoesNotExist:
        return jsonify({404: 'No record with given scientific name'}), 404
    return jsonify(Attracted.objects.get(scientific_name=scientific_name).json()), 200


# delete an attracted item
@attracted_bp.delete('/<scientific_name>')
@require_api_key
def delete_attracted(scientific_name):
    try:
        db_record = Attracted.objects.get(scientific_name=scientific_name)
        db_record.delete()
    except DoesNotExist:
        return jsonify({404: 'No record with given scientific name'}), 404
    return jsonify({200: 'Record deleted'}), 200
