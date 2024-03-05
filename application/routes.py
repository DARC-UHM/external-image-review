import os
import requests
import json

from datetime import datetime, timedelta
from functools import wraps
from flask import render_template, request, redirect, jsonify, send_file
from flask_mail import Mail, Message
from flask_cors import cross_origin
from mongoengine import NotUniqueError, DoesNotExist

from application import app
from schema.comment import Comment, ReviewerCommentList
from schema.reviewer import Reviewer
from schema.annotator import Annotator
from schema.attracted import Attracted


def require_api_key(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        provided_api_key = request.headers.get('API-Key')
        if provided_api_key == app.config.get('API_KEY'):
            return func(*args, **kwargs)
        else:
            app.logger.warning(f'UNAUTHORIZED API ATTEMPT - IP Address: {request.remote_addr}')
            return jsonify({'error': 'Unauthorized'}), 401

    return wrapper


@app.route('/favicon.ico')
def favicon():
    return app.send_static_file('img/favicon.ico')


# add a new comment
@app.post('/comment')
@require_api_key
def add_comment():
    uuid = request.values.get('uuid')
    scientific_name = request.values.get('scientific_name')
    all_localizations = request.values.get('all_localizations')
    sequence = request.values.get('sequence')
    timestamp = request.values.get('timestamp')
    image_url = request.values.get('image_url')
    reviewers = json.loads(request.values.get('reviewers'))
    video_url = request.values.get('video_url')
    annotator = request.values.get('annotator')
    depth = request.values.get('depth')
    lat = request.values.get('lat')
    long = request.values.get('long')
    temperature = request.values.get('temperature')
    oxygen_ml_l = request.values.get('oxygen_ml_l')
    if not uuid or not sequence or not reviewers or not annotator:
        return jsonify({400: 'Missing required values'}), 400
    if scientific_name:  # tator localization
        if 'image' not in request.files:
            return jsonify({400: 'No image provided'}), 400
        img = request.files['image']
        if img.filename == '':
            return jsonify({400: 'No selected file'}), 400
        img.save(os.path.join(app.config.get('TATOR_IMAGE_FOLDER'), img.filename))
        image_url = f'{request.url_root}image/{img.filename}'
    try:
        comment = Comment(
            uuid=uuid,
            scientific_name=scientific_name,
            all_localizations=all_localizations,
            sequence=sequence,
            timestamp=timestamp,
            image_url=image_url,
            unread=False,
            video_url=video_url,
            annotator=annotator,
            depth=depth,
            lat=lat,
            long=long,
            temperature=temperature,
            oxygen_ml_l=oxygen_ml_l,
        )
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
            return jsonify({200: 'No updates made'}), 200
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


# delete a comment given an observation uuid
@app.delete('/comment/<uuid>')
@require_api_key
def delete_comment(uuid):
    try:
        db_record = Comment.objects.get(uuid=uuid)
    except DoesNotExist:
        return jsonify({404: 'No comment records matching given uuid'}), 404
    if db_record['scientific_name']:  # tator localization
        img_name = db_record['image_url'].split('/')[-1]
        try:
            os.remove(os.path.join(os.getcwd(), app.config.get('TATOR_IMAGE_FOLDER'), img_name))
        except FileNotFoundError:
            app.logger.warning(f'Failed to delete image: {img_name}')
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


# returns all comments for a given reviewer
@app.get('/comment/reviewer/<reviewer_name>')
@require_api_key
def get_reviewer_comments(reviewer_name):
    comments = {}
    db_records = Comment.objects(reviewer_comments__reviewer=reviewer_name)
    for record in db_records:
        obj = record.json()
        comments[obj['uuid']] = record.json()
    return jsonify(comments), 200


# returns one comment
@app.get('/comment/get/<uuid>')
@cross_origin()
def get_comment(uuid):
    db_record = Comment.objects(uuid=uuid)
    if not db_record:
        return jsonify({404: 'No comment with given uuid'}), 404
    return jsonify(db_record[0].json()), 200


# update ctd data for all comments in the db
@app.put('/sync-ctd')
@require_api_key
def sync_ctd():
    updated_ctd = json.loads(request.data)
    for uuid in updated_ctd.keys():
        record = Comment.objects.get(uuid=uuid)
        record.update(
            set__depth=str(updated_ctd[uuid]['depth']),
            set__lat=str(updated_ctd[uuid]['lat']),
            set__long=str(updated_ctd[uuid]['long']),
            set__temperature=str(updated_ctd[uuid]['temperature']),
            set__oxygen_ml_l=str(updated_ctd[uuid]['oxygen_ml_l']),
        )
    return jsonify({200: 'CTD synced'}), 200


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
    comments = []
    return_all_comments = request.args.get('all') == 'true'
    reviewer_name = reviewer_name.replace('-', ' ')
    matched_records = Comment.objects(reviewer_comments__reviewer=reviewer_name)
    annotators = set()
    for record in matched_records:
        annotators.add(record.annotator)
        record = record.json()
        # show all comments or only return records that the reviewer has not yet commented on
        if return_all_comments or next((x for x in record['reviewer_comments'] if x['reviewer'] == reviewer_name))['comment'] == '':
            # filter by annotator if specified
            if request.args.getlist('annotator') and record['annotator'] not in request.args.getlist('annotator'):
                continue
            comments.append(record)
            # for VARS annotations, get the record info from the server
            if record['scientific_name'] is None or record['scientific_name'] == '':  # VARS annotation
                with requests.get(f'http://hurlstor.soest.hawaii.edu:8082/anno/v1/annotations/{record["uuid"]}') as r:
                    server_record = r.json()
                    record['concept'] = server_record['concept']
                    # check for "identity-certainty: maybe" and "identity-reference"
                    for association in server_record['associations']:
                        if association['link_name'] == 'identity-certainty':
                            record['id_certainty'] = association['link_value']
                        if association['link_name'] == 'identity-reference':
                            # dive num + id ref to account for duplicate numbers across dives
                            record['id_reference'] = f'{record["sequence"][-2:]}:{association["link_value"]}'
    data = {'comments': comments, 'reviewer': reviewer_name, 'annotators': [annotator for annotator in annotators]}
    return render_template('external_review.html', data=data), 200


# returns number of unread comments, number of total comments, and a list of reviewers with comments in the database
@app.get('/stats')
@require_api_key
def stats():
    active_reviewers = Comment.objects().distinct(field='reviewer_comments.reviewer')
    unread_comments = Comment.objects(unread=True).count()
    total_comments = Comment.objects().count()
    return jsonify({
        'unread_comments': unread_comments,
        'total_comments': total_comments,
        'active_reviewers': active_reviewers,
    }), 200


# route to save reviewer's comments, redirects to success page
@app.post('/save-comments')
def save_comments():
    mail = Mail(app)
    reviewer_name = request.values.get('reviewer')
    annotator_emails = [app.config.get('ADMIN_EMAIL')]
    for annotator in json.loads(request.values.get('annotators').replace('\'', '"')):
        try:
            annotator_emails.append(Annotator.objects.get(name=annotator).email)
        except DoesNotExist:
            pass
    count_success = 0
    list_failures = []
    for uuid in request.values:
        if uuid == reviewer_name or uuid == 'annotators':
            continue
        data = {'comment': request.values.get(uuid)}
        with requests.patch(
                f'{request.url_root}/comment/{reviewer_name}/{uuid}',
                headers={'API-Key': app.config.get('API_KEY')},
                data=data,
        ) as r:
            if r.status_code == 200:
                count_success += 1
            else:
                list_failures.append(uuid)
    if count_success > 0:
        msg = Message(
            f'DARC Review - New Comments from {reviewer_name}',
            sender=app.config.get('MAIL_USERNAME'),
            recipients=annotator_emails,
        )
        msg.body = 'Aloha,\n\n' + \
                   f'{reviewer_name} just added comments to your annotations in the external review database. ' + \
                   f'There are now {Comment.objects(unread=True).count()} total unread comments.\n\n' + \
                   'DARC Review\n'
        mail.send(msg)
        return redirect(f'success?name={reviewer_name}&count={count_success}')
    else:
        return jsonify({500: f'Internal server error - could not update {list_failures}'}), 500


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


@app.get('/image/<image_name>')
def image(image_name):
    file_path = os.path.join(os.getcwd(), app.config.get("TATOR_IMAGE_FOLDER"), image_name)
    if os.path.exists(file_path):
        return send_file(file_path)
    else:
        return jsonify({404: 'Image not found'}), 404


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


@app.errorhandler(404)
def page_not_found(e):
    app.logger.info(f'Tried to access page {request.url} - IP Address: {request.remote_addr}')
    return render_template('404.html'), 404
