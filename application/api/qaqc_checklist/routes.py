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
        checklist = VarsQaqcChecklist(
            sequence_names=sequences,
            multiple_associations=0,
            primary_substrate=0,
            identical_s1_s2=0,
            duplicate_s2=0,
            upon_substrate=0,
            timestamp_substrate=0,
            missing_upon=0,
            missing_ancillary=0,
            ref_id_concept_name=0,
            ref_id_associations=0,
            blank_associations=0,
            suspicious_host=0,
            expected_association=0,
            time_diff_host_upon=0,
            bounding_boxes=0,
            localizations_missing_bounding_box=0,
            unique_fields=0,
        ).save()
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
        checklist = TatorDropcamQaqcChecklist(
            deployment_names=deployments,
            names_accepted=0,
            missing_qualifier=0,
            stet_reason=0,
            tentative_id=0,
            attracted=0,
            non_target_not_attracted=0,
            exists_in_image_refs=0,
            same_name_qualifier=0,
            notes_remarks=0,
            re_examined=0,
            unique_taxa=0,
            media_attributes=0,
        ).save()
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
        checklist = TatorSubQaqcChecklist(
            transect_media_ids=transect_media_ids,
            names_accepted=0,
            missing_qualifier=0,
            stet_reason=0,
            tentative_id=0,
            missing_upon=0,
            upon_not_substrate=0,
            suspicious_host=0,
            time_diff_host_upon=0,
            missing_ancillary=0,
            notes_remarks=0,
            re_examined=0,
            review_sizes=0,
            unique_taxa=0,
            media_attributes=0,
        ).save()
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
