from flask import jsonify, request, current_app
from mongoengine import DoesNotExist

from application.require_api_key import require_api_key
from application.schema.tator_dropcam_qaqc_checklist import TatorDropcamQaqcChecklist
from application.schema.tator_sub_qaqc_checklist import TatorSubQaqcChecklist
from application.schema.vars_qaqc_checklist import VarsQaqcChecklist

from . import qaqc_checklist_bp


# get vars qaqc checklist (based on sequence name)
@qaqc_checklist_bp.get('/vars/<sequences>')
@require_api_key
def vars_qaqc_checklist(sequences):
    if not sequences:
        return jsonify({'error': 'No sequence name provided'}), 400
    try:
        checklist = VarsQaqcChecklist.objects.get(sequence_names=sequences)
    except DoesNotExist:
        # create a new checklist
        checklist = VarsQaqcChecklist(sequence_names=sequences).save()
        current_app.logger.info(f'Created new VARS QA/QC checklist: {sequences}')
    return jsonify(checklist.json()), 200


# update vars qaqc checklist
@qaqc_checklist_bp.patch('/vars/<sequences>')
@require_api_key
def patch_vars_qaqc_checklist(sequences):
    if not sequences:
        return jsonify({'error': 'No sequence name provided'}), 400
    updated_checkbox = request.json
    try:
        checklist = VarsQaqcChecklist.objects.get(sequence_names=sequences)
    except DoesNotExist:
        return jsonify({'error': 'No checklist found for given sequence name'}), 404
    checklist[next(iter(updated_checkbox.keys()))] = next(iter(updated_checkbox.values()))
    checklist.save()
    current_app.logger.info(f'Updated VARS QA/QC checklist: {sequences}')
    return jsonify(checklist.json()), 200


# get tator dropcam qaqc checklist (based on deployment name)
@qaqc_checklist_bp.get('/tator-dropcam/<deployments>')
@require_api_key
def tator_qaqc_checklist(deployments):
    if not deployments:
        return jsonify({'error': 'No deployment name provided'}), 400
    try:
        checklist = TatorDropcamQaqcChecklist.objects.get(deployment_names=deployments)
    except DoesNotExist:
        # create a new checklist
        checklist = TatorDropcamQaqcChecklist(deployment_names=deployments).save()
        current_app.logger.info(f'Created new Tator dropcam QA/QC checklist: {deployments}')
    return jsonify(checklist.json()), 200


# update tator qaqc checklist
@qaqc_checklist_bp.patch('/tator-dropcam/<deployments>')
@require_api_key
def patch_tator_qaqc_checklist(deployments):
    if not deployments:
        return jsonify({'error': 'No deployment name provided'}), 400
    updated_checkbox = request.json
    try:
        checklist = TatorDropcamQaqcChecklist.objects.get(deployment_names=deployments)
    except DoesNotExist:
        return jsonify({'error': 'No checklist found for given deployment name'}), 404
    checklist[next(iter(updated_checkbox.keys()))] = next(iter(updated_checkbox.values()))
    checklist.save()
    current_app.logger.info(f'Updated Tator dropcam QA/QC checklist: {deployments}')
    return jsonify(checklist.json()), 200


# get tator sub qaqc checklist (based on transect media id)
@qaqc_checklist_bp.get('/tator-sub/<transect_media_ids>')
@require_api_key
def tator_sub_qaqc_checklist(transect_media_ids):
    if not transect_media_ids:
        return jsonify({'error': 'No transect media IDs provided'}), 400
    try:
        checklist = TatorSubQaqcChecklist.objects.get(transect_media_ids=transect_media_ids)
    except DoesNotExist:
        # create a new checklist
        checklist = TatorSubQaqcChecklist(transect_media_ids=transect_media_ids).save()
        current_app.logger.info(f'Created new Tator sub QA/QC checklist: {transect_media_ids}')
    return jsonify(checklist.json()), 200


# update tator sub qaqc checklist
@qaqc_checklist_bp.patch('/tator-sub/<transect_media_ids>')
@require_api_key
def patch_tator_sub_qaqc_checklist(transect_media_ids):
    if not transect_media_ids:
        return jsonify({'error': 'No transect media IDs provided'}), 400
    updated_checkbox = request.json
    try:
        checklist = TatorSubQaqcChecklist.objects.get(transect_media_ids=transect_media_ids)
    except DoesNotExist:
        return jsonify({'error': 'No checklist found for given transect media IDs'}), 404
    checklist[next(iter(updated_checkbox.keys()))] = next(iter(updated_checkbox.values()))
    checklist.save()
    current_app.logger.info(f'Updated Tator sub QA/QC checklist: {transect_media_ids}')
    return jsonify(checklist.json()), 200
