from datetime import datetime

import requests
from flask import render_template, request, redirect
from mongoengine import NotUniqueError, DoesNotExist

from application import app
from comment.comment import Comment
from comment.comment_loader import CommentLoader
from translate_substrate import translate_substrate_code


@app.route('/favicon.ico')
def favicon():
    return app.send_static_file('img/favicon.ico')


@app.post('/add_comment')
def add_comment():
    uuid = request.values.get('uuid')
    sequence = request.values.get('sequence')
    timestamp = request.values.get('timestamp')
    image_url = request.values.get('image_url')
    concept = request.values.get('concept')
    reviewer = request.values.get('reviewer')
    video_url = request.values.get('video_url')
    id_certainty = request.values.get('id_certainty')
    id_reference = request.values.get('id_reference')
    upon = request.values.get('upon')
    if not uuid or not sequence or not timestamp or not image_url or not concept or not reviewer:
        return {400: 'Missing required values'}, 400
    try:
        comment = Comment(
            uuid=uuid,
            sequence=sequence,
            timestamp=timestamp,
            image_url=image_url,
            concept=concept,
            reviewer=reviewer,
            video_url=video_url,
            id_certainty=id_certainty,
            id_reference=id_reference,
            upon=upon,
        ).save()
    except NotUniqueError:
        return {409: 'Already a comment record for given uuid'}, 409
    return comment.json(), 201


@app.post('/sync_comments')
def sync_comments():
    # takes a list of sequences, iterates through list and adds all records that have comment associations
    sequences = []
    for value in request.values:
        sequences.append(request.values.get(value))
    comment_loader = CommentLoader(sequences, request.url_root)
    return comment_loader.comments, 200


@app.put('/update_comment/<uuid>')
def update_comment(uuid):
    try:
        db_record = Comment.objects.get(uuid=uuid)
    except DoesNotExist:
        return {404: 'No comment records matching given uuid'}, 404
    db_record.update(set__comment=request.values.get('comment'), set__date_modified=datetime.now)
    return Comment.objects.get(uuid=uuid).json(), 200


@app.put('/update_reviewer/<uuid>')
def update_reviewer(uuid):
    # change the reviewer on a comment TODO
    return ''


@app.delete('/delete_comment/<uuid>')
def delete_record(uuid):
    try:
        db_record = Comment.objects.get(uuid=uuid)
    except DoesNotExist:
        return {404: 'No comment records matching given uuid'}, 404
    db_record.delete()
    return {200: 'Comment deleted'}, 200


@app.get('/get_all_comments')
def get_all_comments():
    comments = []
    db_records = Comment.objects()
    for record in db_records:
        comments.append(record.json())
    return comments, 200


@app.get('/get_sequence_comments/<sequence_num>')
def get_sequence_comments(sequence_num):
    comments = []
    db_records = Comment.objects(sequence=sequence_num)
    for record in db_records:
        comments.append(record.json())
    return comments, 200


@app.get('/get_reviewer_comments/<reviewer_name>')
def get_reviewer_comments(reviewer_name):
    comments = []
    db_records = Comment.objects(reviewer=reviewer_name)
    for record in db_records:
        comments.append(record.json())
    return comments, 200


@app.get('/review/<reviewer_name>')
def review(reviewer_name):
    comments = []
    matched_records = Comment.objects(reviewer=reviewer_name)
    for record in matched_records:
        record = record.json()
        if 'upon' in record.keys():
            record['upon'] = translate_substrate_code(record['upon'])
        comments.append(record)
        # check if concept on the server is different than what we have saved
        with requests.get(f'http://hurlstor.soest.hawaii.edu:8082/anno/v1/annotations/{record["uuid"]}') as r:
            server_record = r.json()
        if 'concept' not in record.keys() or record['concept'] != server_record['concept']:
            record['concept'] = server_record['concept']
    data = {'comments': comments, 'reviewer': reviewer_name}
    return render_template('external_review.html', data=data), 200


@app.post('/save_comments')
def save_comments():
    reviewer_name = request.values.get('reviewer')
    count_success = 0
    list_failures = []
    for value in request.values:
        data = {'comment': request.values.get(value)}
        with requests.put(f'{request.url_root}/update_comment/{value}', data=data) as r:
            if r.status_code == 200:
                count_success += 1
            else:
                list_failures.append(value)
    if count_success > 0:
        return redirect(f'success?name={reviewer_name}&count={count_success}')
    else:
        return {500: f'Internal server error - could not update {list_failures}'}, 500


@app.get('/success')
def success():
    name = request.args.get('name')
    count = request.args.get('count')
    data = {'name': name, 'count': count}
    return render_template('save_success.html', data=data), 200


@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404
