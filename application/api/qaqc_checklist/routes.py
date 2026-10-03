from flask import jsonify, request, current_app
from mongoengine import DoesNotExist, ValidationError

from application.require_api_key import require_api_key
from application.schema.tator_dropcam_qaqc_checklist import TatorDropcamQaqcChecklist
from application.schema.tator_sub_qaqc_checklist import TatorSubQaqcChecklist
from application.schema.vars_qaqc_checklist import VarsQaqcChecklist

from . import qaqc_checklist_bp

CHECKLISTS = {
    'vars': VarsQaqcChecklist,
    'tator-dropcam': TatorDropcamQaqcChecklist,
    'tator-sub': TatorSubQaqcChecklist,
}


def _unknown_type_response(checklist_type):
    return jsonify({'error': f'Unknown checklist type: {checklist_type}'}), 404


# get a qaqc checklist, creating it if it doesn't exist
@qaqc_checklist_bp.get('/<checklist_type>/<key>')
@require_api_key
def get_qaqc_checklist(checklist_type, key):
    if checklist_type not in CHECKLISTS:
        return _unknown_type_response(checklist_type)
    model = CHECKLISTS[checklist_type]
    try:
        checklist = model.objects.get(**{model.KEY_FIELD: key})
    except DoesNotExist:
        checklist = model(**{model.KEY_FIELD: key}).save()
        current_app.logger.info(f'Created new {model.LABEL} QA/QC checklist: {key}')
    return jsonify(checklist.json()), 200


# update a single field on a qaqc checklist
@qaqc_checklist_bp.patch('/<checklist_type>/<key>')
@require_api_key
def patch_qaqc_checklist(checklist_type, key):
    if checklist_type not in CHECKLISTS:
        return _unknown_type_response(checklist_type)
    model = CHECKLISTS[checklist_type]
    body = request.get_json(silent=True)
    if not isinstance(body, dict) or len(body) != 1:
        return jsonify({'error': 'Body must be a single key/value pair'}), 400
    field, value = next(iter(body.items()))
    if field not in set(model._fields) - {'id', model.KEY_FIELD}:
        return jsonify({'error': f'Not a {model.LABEL} checklist field: {field}'}), 400
    try:
        checklist = model.objects.get(**{model.KEY_FIELD: key})
    except DoesNotExist:
        return jsonify({'error': f'No {model.LABEL} checklist found for given key'}), 404
    checklist[field] = value
    try:
        checklist.save()
    except ValidationError as e:
        return jsonify({'error': f'Invalid value for {field}: {e.message}'}), 400
    current_app.logger.info(f'Updated {model.LABEL} QA/QC checklist: {key}')
    return jsonify(checklist.json()), 200
