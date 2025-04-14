from flask import jsonify, request, current_app
from mongoengine import NotUniqueError, DoesNotExist

from application.require_api_key import require_api_key
from schema.reviewer import Reviewer
from . import reviewer_bp


# get all reviewers
@reviewer_bp.get('/all')
@require_api_key
def get_all_reviewers():
    return jsonify([record.json() for record in Reviewer.objects()]), 200


# add a new reviewer
@reviewer_bp.post('')
@require_api_key
def add_reviewer():
    name = request.values.get('name')
    phylum = request.values.get('phylum')
    if not name or not phylum:
        return jsonify({400: 'Missing required values'}), 400
    try:
        reviewer = Reviewer(
            name=name,
            phylum=phylum,
            email=request.values.get('email'),
            organization=request.values.get('organization'),
            focus=request.values.get('focus'),
        ).save()
    except NotUniqueError:
        return jsonify({409: 'There is already a reviewer with this name'}), 409
    current_app.logger.info(f'Added new reviewer to database: {name}')
    return jsonify(reviewer.json()), 201


# update a reviewer's information
@reviewer_bp.patch('/<old_name>')  # this should be PUT but too lazy to change
@require_api_key
def update_reviewer_info(old_name):
    new_name = request.values.get('new_name', old_name)
    try:
        db_record = Reviewer.objects.get(name=old_name)
    except DoesNotExist:
        return jsonify({404: 'No reviewer records found with matching name'}), 404
    db_record.update(
        set__name=new_name,
        set__email=request.values.get('email', ''),
        set__organization=request.values.get('organization', ''),
        set__phylum=request.values.get('phylum', ''),
        set__focus=request.values.get('focus', ''),
    )
    return jsonify(Reviewer.objects.get(name=new_name).json()), 200


# delete a reviewer
@reviewer_bp.delete('/<name>')
@require_api_key
def delete_reviewer(name):
    try:
        db_record = Reviewer.objects.get(name=name)
        db_record.delete()
    except DoesNotExist:
        return jsonify({404: 'No comment records matching given uuid'}), 404
    current_app.logger.info(f'Deleted reviewer from database: {name}')
    return jsonify({200: 'Reviewer deleted'}), 200
