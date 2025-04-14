from flask import jsonify, request, current_app
from mongoengine import DoesNotExist

from application.require_api_key import require_api_key
from schema.tator_qaqc_checklist import TatorQaqcChecklist
from schema.vars_qaqc_checklist import VarsQaqcChecklist

from . import qaqc_checklist_bp


# get vars qaqc checklist (based on sequence name)
@qaqc_checklist_bp.get('/vars-qaqc-checklist/<sequences>')
@require_api_key
def vars_qaqc_checklist(sequences):
    if not sequences:
        return jsonify({400: 'No sequence name provided'}), 400
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
            unique_fields=0,
        ).save()
        current_app.logger.info(f'Created new VARS QA/QC checklist: {sequences}')
    return jsonify(checklist.json()), 200


# update vars qaqc checklist
@qaqc_checklist_bp.patch('/vars-qaqc-checklist/<sequences>')
@require_api_key
def patch_vars_qaqc_checklist(sequences):
    if not sequences:
        return jsonify({400: 'No sequence name provided'}), 400
    updated_checkbox = request.json
    checklist = VarsQaqcChecklist.objects.get(sequence_names=sequences)
    checklist[next(iter(updated_checkbox.keys()))] = next(iter(updated_checkbox.values()))
    checklist.save()
    current_app.logger.info(f'Updated VARS QA/QC checklist: {sequences}')
    return jsonify(checklist.json()), 200


# get tator qaqc checklist (based on deployment name)
@qaqc_checklist_bp.get('/tator-qaqc-checklist/<deployments>')
@require_api_key
def tator_qaqc_checklist(deployments):
    if not deployments:
        return jsonify({400: 'No deployment name provided'}), 400
    try:
        checklist = TatorQaqcChecklist.objects.get(deployment_names=deployments)
    except DoesNotExist:
        # create a new checklist
        checklist = TatorQaqcChecklist(
            deployment_names=deployments,
            names_accepted=0,
            missing_qualifier=0,
            stet_reason=0,
            tentative_id=0,
            attracted=0,
            non_target_not_attracted=0,
            same_name_qualifier=0,
            notes_remarks=0,
            re_examined=0,
            unique_taxa=0,
            media_attributes=0,
        ).save()
        current_app.logger.info(f'Created new Tator QA/QC checklist: {deployments}')
    return jsonify(checklist.json()), 200


# update tator qaqc checklist
@qaqc_checklist_bp.patch('/tator-qaqc-checklist/<deployments>')
@require_api_key
def patch_tator_qaqc_checklist(deployments):
    if not deployments:
        return jsonify({400: 'No deployment name provided'}), 400
    updated_checkbox = request.json
    checklist = TatorQaqcChecklist.objects.get(deployment_names=deployments)
    checklist[next(iter(updated_checkbox.keys()))] = next(iter(updated_checkbox.values()))
    checklist.save()
    current_app.logger.info(f'Updated Tator QA/QC checklist: {deployments}')
    return jsonify(checklist.json()), 200
