import base64
import json
import os
import re
import requests
import threading
import traceback

from datetime import datetime, timedelta
from functools import wraps
from flask import render_template, request, redirect, jsonify, send_file, Response
from flask_mail import Mail, Message
from flask_cors import cross_origin
from json import JSONDecodeError
from mongoengine import NotUniqueError, DoesNotExist

from application import app
from application.vars_summary import VarsSummary
from schema.comment import Comment, ReviewerCommentList
from schema.dropcam_field_book import DropcamFieldBook
from schema.reviewer import Reviewer
from schema.annotator import Annotator
from schema.attracted import Attracted
from schema.tator_qaqc_checklist import TatorQaqcChecklist
from schema.vars_qaqc_checklist import VarsQaqcChecklist


def require_api_key(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        provided_api_key = request.headers.get('API-Key')
        if provided_api_key == app.config.get('API_KEY'):
            return func(*args, **kwargs)
        else:
            app.logger.warning(f'UNAUTHORIZED API ATTEMPT - IP Address: {request.remote_addr}')
            app.logger.info(f'URL: {request.url}')
            return jsonify({'error': 'Unauthorized'}), 401
    return wrapper


def send_email(msg):
    with app.app_context():
        mail = Mail(app)
        mail.send(msg)


@app.route('/favicon.ico')
def favicon():
    return app.send_static_file('img/favicon.ico')


# add a new comment
@app.post('/comment')
@require_api_key
def add_comment():
    comment = {}
    reviewers = json.loads(request.values.get('reviewers'))
    fields = ['uuid', 'all_localizations', 'sequence', 'timestamp', 'image_url', 'video_url', 'id_reference',
              'annotator', 'section_id']
    for field in fields:
        value = request.values.get(field)
        if value is not None and value != '':
            comment[field] = value
    if not comment['uuid'] or not comment['sequence'] or not reviewers or not comment['annotator']:
        return jsonify({400: 'Missing required values'}), 400
    if comment.get('all_localizations'):  # tator localization
        comment['sequence'] = comment['sequence'].replace('-', '_')
    try:
        comment = Comment(**comment)
        for reviewer in reviewers:
            comment.reviewer_comments.append(
                ReviewerCommentList(
                    reviewer=reviewer,
                    comment='',
                    date_modified=(datetime.now() - timedelta(hours=10)),
                )
            )
        comment.save()
    except NotUniqueError:
        return jsonify({409: 'Already a comment record for given uuid'}), 409
    return jsonify(comment.json()), 201


@app.get('/tator-frame/<media_id>/<frame_number>')
def tator_frame(media_id, frame_number):
    url = f'{app.config.get("TATOR_URL")}/rest/GetFrame/{media_id}?frames={frame_number}'
    if request.values.get('preview'):
        url += '&quality=650'
    res = requests.get(
        url=url,
        headers={'Authorization': f'Token {os.environ.get("TATOR_TOKEN")}'}
    )
    if res.status_code == 200:
        base64_image = base64.b64encode(res.content).decode('utf-8')
        return Response(base64.b64decode(base64_image), content_type='image/png'), 200
    return '', 500


@app.get('/tator-video/<media_id>')
def tator_video(media_id):
    req = requests.get(
        url=f'https://cloud.tator.io/rest/Media/{media_id}?presigned=3600',
        headers={
            'accept': 'application/json',
            'Authorization': f'Token {os.environ.get("TATOR_TOKEN")}',
        }
    )
    try:
        media = req.json()
    except JSONDecodeError:
        return jsonify({404: 'No media found'}), 404
    return redirect(media['media_files']['archival'][0]['path'])


# update a comment's text given a reviewer and an observation uuid
@app.patch('/comment/<reviewer>/<uuid>')
@require_api_key
def update_comment(reviewer, uuid):
    try:
        db_record = Comment.objects.get(uuid=uuid)
    except DoesNotExist:
        return jsonify({404: 'No comment records matching given uuid'}), 404
    for reviewer_comment in db_record.reviewer_comments:
        if reviewer_comment['reviewer'] == reviewer:
            if reviewer_comment['comment'] != request.values.get('comment'):
                reviewer_comment['comment'] = request.values.get('comment')
                reviewer_comment['date_modified'] = (datetime.now() - timedelta(hours=10))
                db_record.unread = True
                db_record.save()
                return jsonify(Comment.objects.get(uuid=uuid).json()), 200
            return jsonify({304: 'No updates made'}), 304
    return jsonify({404: 'No comment records matching given reviewer'}), 404


# update a comment's reviewers given an observation uuid
@app.put('/comment/reviewers/<uuid>')
@require_api_key
def update_comment_reviewer(uuid):
    try:
        db_record = Comment.objects.get(uuid=uuid)
    except DoesNotExist:
        return jsonify({404: 'No comment records matching given uuid'}), 404
    reviewers = json.loads(request.values.get('reviewers'))
    temp_reviewer_comments = []
    for reviewer_comment in db_record.reviewer_comments:
        if reviewer_comment['reviewer'] in reviewers:
            temp_reviewer_comments.append(reviewer_comment)
            reviewers.remove(reviewer_comment['reviewer'])
    for reviewer in reviewers:
        temp_reviewer_comments.append(
            ReviewerCommentList(
                reviewer=reviewer,
                comment='',
                date_modified=(datetime.now() - timedelta(hours=10)),
            )
        )
    db_record.reviewer_comments = temp_reviewer_comments
    db_record.save()
    return jsonify(Comment.objects.get(uuid=uuid).json()), 200


# mark a comment as read
@app.put('/comment/mark-read/<uuid>')
def mark_comment_read(uuid):
    try:
        db_record = Comment.objects.get(uuid=uuid)
    except DoesNotExist:
        return jsonify({404: 'No comment records matching given uuid'}), 404
    db_record.update(
        unread=False,
    )
    return jsonify(Comment.objects.get(uuid=uuid).json()), 200


# mark a comment as unread
@app.put('/comment/mark-unread/<uuid>')
def mark_comment_unread(uuid):
    try:
        db_record = Comment.objects.get(uuid=uuid)
    except DoesNotExist:
        return jsonify({404: 'No comment records matching given uuid'}), 404
    db_record.update(
        unread=True,
    )
    return jsonify(Comment.objects.get(uuid=uuid).json()), 200


# delete a comment given an observation uuid
@app.delete('/comment/<uuid>')
@require_api_key
def delete_comment(uuid):
    try:
        db_record = Comment.objects.get(uuid=uuid)
    except DoesNotExist:
        return jsonify({404: 'No comment records matching given uuid'}), 404
    db_record.delete()
    return jsonify({200: 'Comment deleted'}), 200


# returns all comments saved in the database
@app.get('/comment/all')
@require_api_key
def get_all_comments():
    comments = {}
    db_records = Comment.objects()
    for record in db_records:
        obj = record.json()
        comments[obj['uuid']] = record.json()
    return jsonify(comments), 200


# returns all unread comments
@app.get('/comment/unread')
@require_api_key
def get_unread_comments():
    comments = {}
    db_records = Comment.objects(unread=True)
    for record in db_records:
        obj = record.json()
        comments[obj['uuid']] = record.json()
    return jsonify(comments), 200


# returns all read comments
@app.get('/comment/read')
@require_api_key
def get_read_comments():
    comments = {}
    # get comments with unread=False and each reviewer_comment.comment != ''
    db_records = Comment.objects(unread=False, reviewer_comments__comment__ne='')
    for record in db_records:
        obj = record.json()
        comments[obj['uuid']] = record.json()
    return jsonify(comments), 200


# returns all comments in a given sequence
@app.get('/comment/sequence/<sequence_num>')
@require_api_key
def get_sequence_comments(sequence_num):
    comments = {}
    db_records = Comment.objects(sequence=sequence_num)
    for record in db_records:
        obj = record.json()
        comments[obj['uuid']] = record.json()
    return jsonify(comments), 200


# returns comments for a given reviewer
@app.get('/comment/reviewer/<reviewer_name>')
@require_api_key
def get_reviewer_comments(reviewer_name):
    unread_comments = Comment.objects(unread=True, reviewer_comments__reviewer=reviewer_name).count()
    read_comments = Comment.objects(
        unread=False,
        reviewer_comments__comment__ne='',
        reviewer_comments__reviewer=reviewer_name,
    ).count()
    total_comments = Comment.objects(reviewer_comments__reviewer=reviewer_name).count()
    comments = {}
    if request.args.get('unread') == 'true':
        db_records = Comment.objects(unread=True, reviewer_comments__reviewer=reviewer_name)
    elif request.args.get('read') == 'true':
        db_records = Comment.objects(
            unread=False,
            reviewer_comments__comment__ne='',
            reviewer_comments__reviewer=reviewer_name,
        )
    else:
        db_records = Comment.objects(reviewer_comments__reviewer=reviewer_name)
    for record in db_records:
        obj = record.json()
        comments[obj['uuid']] = record.json()
    return jsonify({
        'unread_comments': unread_comments,
        'read_comments': read_comments,
        'total_comments': total_comments,
        'comments': comments,
    }), 200


# returns one comment
@app.get('/comment/get/<uuid>')
@cross_origin()
def get_comment(uuid):
    db_record = Comment.objects(uuid=uuid)
    if not db_record:
        return jsonify({404: 'No comment with given uuid'}), 404
    return jsonify(db_record[0].json()), 200


# add a new reviewer to the database
@app.post('/reviewer')
@require_api_key
def add_reviewer():
    name = request.values.get('name')
    email = request.values.get('email')
    organization = request.values.get('organization')
    phylum = request.values.get('phylum')
    focus = request.values.get('focus')
    if not name or not phylum:
        return jsonify({400: 'Missing required values'}), 400
    try:
        reviewer = Reviewer(
            name=name,
            email=email,
            organization=organization,
            phylum=phylum,
            focus=focus
        ).save()
    except NotUniqueError:
        return jsonify({409: 'Already a comment record for given uuid'}), 409
    return jsonify(reviewer.json()), 201


# update a reviewer's information
@app.patch('/reviewer/<old_name>')
@require_api_key
def update_reviewer_info(old_name):
    new_name = request.values.get('new_name')  # if the name didn't change, this will be the same as old_name
    email = request.values.get('email')
    organization = request.values.get('organization')
    phylum = request.values.get('phylum')
    focus = request.values.get('focus')
    try:
        db_record = Reviewer.objects.get(name=old_name)
    except DoesNotExist:
        return jsonify({404: 'No reviewer records found with matching name'}), 404
    db_record.update(
        set__name=new_name,
        set__email=email or '',
        set__organization=organization or '',
        set__phylum=phylum or '',
        set__focus=focus or ''
    )
    return jsonify(Reviewer.objects.get(name=new_name).json()), 200


# delete a reviewer
@app.delete('/reviewer/<name>')
@require_api_key
def delete_reviewer(name):
    try:
        db_record = Reviewer.objects.get(name=name)
        db_record.delete()
    except DoesNotExist:
        return jsonify({404: 'No comment records matching given uuid'}), 404
    return jsonify({200: 'Reviewer deleted'}), 200


# returns all reviewers saved in the database
@app.get('/reviewer/all')
@require_api_key
def get_all_reviewers():
    reviewers = []
    db_records = Reviewer.objects()
    for record in db_records:
        reviewers.append(record.json())
    return jsonify(reviewers), 200


# the link to share with external reviewers
@app.get('/review/<reviewer_name>')
def review(reviewer_name):
    app.logger.info(f'Access {reviewer_name}\'s review page - IP Address: {request.remote_addr}')
    app.logger.info(request.url)
    comments = []
    return_all_comments = request.args.get('all') == 'true'
    reviewer_name = reviewer_name.replace('-', ' ')
    matched_records = Comment.objects(reviewer_comments__reviewer=reviewer_name).order_by('sequence')
    for record in matched_records:
        record = record.json()
        if return_all_comments or next((x for x in record['reviewer_comments'] if x['reviewer'] == reviewer_name))['comment'] == '':
            # show all comments or only return records that the reviewer has not yet commented on
            if request.args.getlist('annotator') and record['annotator'] not in request.args.getlist('annotator'):
                # filter by annotator if specified
                continue
            if request.args.get('sequence') and request.args.get('sequence') not in record['sequence']:
                # filter by sequence (aka dive/deployment) if specified
                continue
            comments.append(record)
            if not record.get('all_localizations') or record['all_localizations'] == '':  # VARS annotation
                # for VARS annotations, get the record info from VARS server
                with requests.get(f'{app.config.get("HURLSTOR_URL")}:8082/v1/annotations/{record["uuid"]}') as r:
                    try:
                        server_record = r.json()
                        record['concept'] = server_record['concept']
                    except (JSONDecodeError, KeyError):
                        comments = [x for x in comments if x['uuid'] != record['uuid']]  # remove record from list
                        app.logger.error(f'Failed to decode JSON for {record["uuid"]} (reviewer: {reviewer_name})')
                        continue
                    if server_record.get('associations'):
                        # check for "identity-certainty: maybe" and "identity-reference"
                        for association in server_record['associations']:
                            if association['link_name'] == 'identity-certainty':
                                record['id_certainty'] = association['link_value']
                            elif association['link_name'] == 'identity-reference':
                                # dive num + id ref to account for duplicate numbers across dives
                                record['id_reference'] = f'{record["sequence"][-2:]}:{association["link_value"]}'
                            elif association['link_name'] == 'sample-reference':
                                record['sample_reference'] = association['link_value']
                    if server_record.get('ancillary_data'):
                        # get ctd
                        for ancillary_data in server_record['ancillary_data']:
                            if ancillary_data == 'latitude':
                                record['lat'] = server_record['ancillary_data']['latitude']
                            elif ancillary_data == 'longitude':
                                record['long'] = server_record['ancillary_data']['longitude']
                            elif ancillary_data == 'depth_meters':
                                record['depth'] = server_record['ancillary_data']['depth_meters']
                            elif ancillary_data == 'temperature_celsius':
                                record['temperature'] = server_record['ancillary_data']['temperature_celsius']
                            elif ancillary_data == 'oxygen_ml_l':
                                record['oxygen_ml_l'] = server_record['ancillary_data']['oxygen_ml_l']

            else:
                # for Tator annotations, get updated localization from tator, get depth, lat, long from local db
                res = requests.get(
                    url=f'{app.config.get("TATOR_URL")}/rest/Localization/45/{record["uuid"]}',
                    headers={'Authorization': f'Token {os.environ.get("TATOR_TOKEN")}'}
                )
                updated_localization = res.json()
                record['id_certainty'] = updated_localization['attributes']['IdentificationRemarks']
                record['image_url'] = f'{request.url_root}/tator-frame/{updated_localization["media"]}/{updated_localization["frame"]}?preview=true'
                record['concept'] = f'{updated_localization["attributes"]["Scientific Name"]}'
                record['depth'] = updated_localization['attributes'].get('Depth')
                record['temperature'] = updated_localization['attributes'].get('DO Temperature (celsius)')
                record['oxygen_ml_l'] = updated_localization['attributes'].get('DO Concentration Salin Comp (mol per L)')
                if updated_localization['attributes']['Tentative ID'] != '':
                    record['concept'] += f' ({updated_localization["attributes"]["Tentative ID"]}?)'
                try:
                    expedition = DropcamFieldBook.objects.get(section_id=record['section_id']).json()
                except DoesNotExist:
                    print(f'No expedition found for {record["section_id"]}')
                    continue
                # find deployment with matching sequence
                deployment = next((x for x in expedition['deployments'] if x['deployment_name'] == record['sequence']), None)
                if deployment is None:
                    continue
                record['expedition_name'] = expedition['expedition_name']
                record['lat'] = deployment['lat']
                record['long'] = deployment['long']
                record['bait_type'] = deployment['bait_type']
                if not record['depth']:
                    record['depth'] = deployment['depth_m']

    data = {'comments': comments, 'reviewer': reviewer_name}
    return render_template('external_review.html', data=data), 200


# returns number of unread comments, number of total comments, and a list of reviewers with comments in the database
@app.get('/stats')
@require_api_key
def stats():
    active_reviewers = Comment.objects().distinct(field='reviewer_comments.reviewer')
    unread_comments = Comment.objects(unread=True).count()
    read_comments = Comment.objects(unread=False, reviewer_comments__comment__ne='').count()
    total_comments = Comment.objects().count()
    return jsonify({
        'unread_comments': unread_comments,
        'read_comments': read_comments,
        'total_comments': total_comments,
        'active_reviewers': active_reviewers,
    }), 200


@app.get('/stats/vars/<sequence_num>')
def sequence_stats(sequence_num):
    app.logger.info(f'Got stats for VARS: {sequence_num} - IP Address: {request.remote_addr}')
    if not sequence_num:
        return jsonify({400: 'No sequence number provided'}), 400
    summary = VarsSummary(sequence_num)
    if not summary.matched_sequences:
        return jsonify({404: 'No sequences in VARS match given sequence number'}), 404
    summary.get_summary()
    comments = Comment.objects(sequence=re.compile(f'.*{sequence_num}.*'))
    reviewers_responded = set()
    for comment in comments:
        comment = comment.json()
        for reviewer_comment in comment['reviewer_comments']:
            if reviewer_comment['comment'] == '':
                continue
            else:
                reviewers_responded.add(reviewer_comment['reviewer'])
    return jsonify({
        'date': summary.date,
        'annotators': list(summary.annotators),
        'dive_count': len(summary.matched_sequences),
        'annotation_count': summary.annotation_count,
        'individual_count': summary.individual_count,
        'unique_taxa_individuals': summary.unique_taxa_individuals,
        'image_count': summary.image_count,
        'video_hours': round(summary.video_millis / 1000 / 60 / 60, 2),
        'phylum_counts': summary.phylum_counts,
        'reviewers_responded': list(reviewers_responded),
    }), 200


@app.get('/summary/vars/<sequence_num>')
def summary(sequence_num):
    return render_template('vars_summary.html', sequence_num=sequence_num), 200


# route to save reviewer's comments, redirects to success page
@app.post('/save-comments')
def save_comments():
    reviewer_name = request.values.get('reviewer')
    comments = json.loads(request.values.get('comments'))
    annotator_emails = [app.config.get('ADMIN_EMAIL')]
    count_success = 0
    list_failures = []
    for annotator in Annotator.objects():
        annotator_emails.append(annotator.email)  # just add all annotators to the email list
    for comment in comments:
        res = requests.patch(
                f'{request.url_root}/comment/{reviewer_name}/{comment["uuid"]}',
                headers={'API-Key': app.config.get('API_KEY')},
                data={'comment': comment["comment"]},
        )
        if res.status_code == 200:
            count_success += 1
        elif res.status_code == 304:
            pass
        else:
            list_failures.append(comment['uuid'])
    if count_success > 0:
        msg = Message(
            f'DARC Review - New Comments from {reviewer_name}',
            sender=app.config.get('MAIL_USERNAME'),
            recipients=annotator_emails,
        )
        msg.body = 'Aloha,\n\n' + \
               f'{reviewer_name} just added {count_success} new comments to the external review database. ' + \
               f'There are now {Comment.objects(unread=True).count()} total unread comments.\n\n' + \
               'DARC Review\n'
        email_thread = threading.Thread(target=send_email, args=(msg,))
        email_thread.start()
        return redirect(f'success?name={reviewer_name}&count={count_success}')
    if list_failures:
        app.logger.error(f'Failed to update comments for {list_failures}')
        return jsonify({500: f'Internal server error - could not update {list_failures}'}), 500
    return redirect(f'success?name={reviewer_name}&count={count_success}')


# displays a save success page
@app.get('/success')
def success():
    name = request.args.get('name')
    count = request.args.get('count')
    data = {'name': name, 'count': count}
    return render_template('save_success.html', data=data), 200


@app.get('/video')
def video():
    data = {'link': request.args.get('link'), 'time': request.args.get('time')}
    return render_template('video.html', data=data), 200


@app.get('/attracted')
def get_attracted():
    return jsonify({attracted.scientific_name: attracted.attracted for attracted in Attracted.objects()}), 200


@app.post('/attracted')
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


@app.patch('/attracted/<scientific_name>')
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


@app.delete('/attracted/<scientific_name>')
@require_api_key
def delete_attracted(scientific_name):
    try:
        db_record = Attracted.objects.get(scientific_name=scientific_name)
        db_record.delete()
    except DoesNotExist:
        return jsonify({404: 'No record with given scientific name'}), 404
    return jsonify({200: 'Record deleted'}), 200


@app.get('/vars-qaqc-checklist/<sequences>')
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
    return jsonify(checklist.json()), 200


@app.patch('/vars-qaqc-checklist/<sequences>')
@require_api_key
def patch_vars_qaqc_checklist(sequences):
    if not sequences:
        return jsonify({400: 'No sequence name provided'}), 400
    updated_checkbox = request.json
    checklist = VarsQaqcChecklist.objects.get(sequence_names=sequences)
    checklist[next(iter(updated_checkbox.keys()))] = next(iter(updated_checkbox.values()))
    checklist.save()
    return jsonify(checklist.json()), 200


@app.get('/tator-qaqc-checklist/<deployments>')
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
    return jsonify(checklist.json()), 200


@app.patch('/tator-qaqc-checklist/<deployments>')
@require_api_key
def patch_tator_qaqc_checklist(deployments):
    if not deployments:
        return jsonify({400: 'No deployment name provided'}), 400
    updated_checkbox = request.json
    checklist = TatorQaqcChecklist.objects.get(deployment_names=deployments)
    checklist[next(iter(updated_checkbox.keys()))] = next(iter(updated_checkbox.values()))
    checklist.save()
    return jsonify(checklist.json()), 200


@app.patch('/video-url/<uuid>')
@require_api_key
def update_video_url(uuid):
    video_url = request.values.get('video_url')
    if not video_url:
        return jsonify({400: 'No video url provided'}), 400
    try:
        db_record = Comment.objects.get(uuid=uuid)
        db_record.update(set__video_url=video_url)
    except DoesNotExist:
        return jsonify({404: 'No record with given uuid'}), 404
    return jsonify(Comment.objects.get(uuid=uuid).json()), 200


@app.get('/dropcam-fieldbook/<section_id>')
@require_api_key
def get_dropcam_field_book(section_id):
    try:
        return jsonify(DropcamFieldBook.objects.get(section_id=section_id).json()), 200
    except DoesNotExist:
        return jsonify({404: 'No record matching given section id'}), 404


@app.post('/dropcam-fieldbook')
@require_api_key
def add_dropcam_field_book():
    try:
        expedition_fieldbook = request.json
        field_book = DropcamFieldBook(
            section_id=expedition_fieldbook['section_id'],
            expedition_name=expedition_fieldbook['expedition_name'],
            deployments=[
                {
                    'deployment_name': deployment['deployment_name'],
                    'lat': deployment['lat'],
                    'long': deployment['long'],
                    'depth_m': deployment['depth_m'],
                    'bait_type': deployment['bait_type'],
                }
                for deployment in expedition_fieldbook['deployments']
            ]
        ).save()
    except JSONDecodeError:
        return jsonify({400: 'Invalid JSON'}), 400
    except KeyError:
        return jsonify({400: 'Missing required values'}), 400
    except NotUniqueError:
        # delete current record and replace with new one
        expedition_fieldbook = request.json
        DropcamFieldBook.objects.get(section_id=expedition_fieldbook['section_id']).delete()
        field_book = DropcamFieldBook(
            section_id=expedition_fieldbook['section_id'],
            expedition_name=expedition_fieldbook['expedition_name'],
            deployments=[
                {
                    'deployment_name': deployment['deployment_name'],
                    'lat': deployment['lat'],
                    'long': deployment['long'],
                    'depth_m': deployment['depth_m'],
                    'bait_type': deployment['bait_type'],
                }
                for deployment in expedition_fieldbook['deployments']
            ]
        ).save()
        return jsonify(field_book.json()), 200
    return jsonify(field_book.json()), 201


@app.errorhandler(404)
def page_not_found(e):
    app.logger.info(f'Tried to access page {request.url} - IP Address: {request.remote_addr}')
    return render_template('404.html'), 404


@app.errorhandler(Exception)
def internal_server_error(e):
    app.logger.error(f'Internal server error - IP Address: {request.remote_addr}')
    app.logger.error(type(e).__name__)
    app.logger.error(e)
    app.logger.error(traceback.format_exc())
    return render_template('500.html'), 500
