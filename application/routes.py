import requests

from datetime import datetime, timedelta
from flask import render_template, request, redirect
from mongoengine import NotUniqueError, DoesNotExist

from application import app
from schema.comment import Comment
from schema.reviewer import Reviewer


@app.route('/favicon.ico')
def favicon():
    return app.send_static_file('img/favicon.ico')


# add a new comment
@app.post('/comment/add')
def add_comment():
    uuid = request.values.get('uuid')
    sequence = request.values.get('sequence')
    timestamp = request.values.get('timestamp')
    image_url = request.values.get('image_url')
    concept = request.values.get('concept')
    reviewer = request.values.get('reviewer')
    video_url = request.values.get('video_url')
    annotator = request.values.get('annotator')
    depth = request.values.get('depth')
    lat = request.values.get('lat')
    long = request.values.get('long')
    if not uuid or not sequence or not timestamp or not image_url or not concept or not reviewer or not annotator:
        return {400: 'Missing required values'}, 400
    try:
        comment = Comment(
            uuid=uuid,
            sequence=sequence,
            timestamp=timestamp,
            image_url=image_url,
            concept=concept,
            reviewer=reviewer,
            unread=False,
            video_url=video_url,
            annotator=annotator,
            depth=depth,
            lat=lat,
            long=long,
        ).save()
    except NotUniqueError:
        return {409: 'Already a comment record for given uuid'}, 409
    return comment.json(), 201


# update a comment's text given an observation uuid
@app.put('/comment/update/<uuid>')
def update_comment(uuid):
    try:
        db_record = Comment.objects.get(uuid=uuid)
    except DoesNotExist:
        return {404: 'No comment records matching given uuid'}, 404
    if db_record.comment != request.values.get('comment'):
        db_record.update(
            set__comment=request.values.get('comment'),
            set__date_modified=(datetime.now() - timedelta(hours=10)),
            set__unread=True
        )
        return Comment.objects.get(uuid=uuid).json(), 200
    return 'No updates made', 200


# update a comment's reviewer given an observation uuid
@app.put('/comment/update-reviewer/<uuid>')
def update_comment_reviewer(uuid):
    try:
        db_record = Comment.objects.get(uuid=uuid)
    except DoesNotExist:
        return {404: 'No comment records matching given uuid'}, 404
    db_record.update(
        set__reviewer=request.values.get('reviewer'),
        set__date_modified=(datetime.now() - timedelta(hours=10))
    )
    return Comment.objects.get(uuid=uuid).json(), 200


# mark a comment as read
@app.put('/comment/mark-read/<uuid>')
def mark_comment_read(uuid):
    try:
        db_record = Comment.objects.get(uuid=uuid)
    except DoesNotExist:
        return {404: 'No comment records matching given uuid'}, 404
    db_record.update(
        set__unread=False,
    )
    return Comment.objects.get(uuid=uuid).json(), 200


# delete a comment given an observation uuid
@app.delete('/comment/delete/<uuid>')
def delete_comment(uuid):
    try:
        db_record = Comment.objects.get(uuid=uuid)
    except DoesNotExist:
        return {404: 'No comment records matching given uuid'}, 404
    db_record.delete()
    return {200: 'Comment deleted'}, 200


# returns all comments saved in the database
@app.get('/comment/all')
def get_all_comments():
    comments = {}
    db_records = Comment.objects()
    for record in db_records:
        obj = record.json()
        comments[obj['uuid']] = {
            'comment': obj['comment'],
            'date_modified': obj['date_modified'],
            'image_url': obj['image_url'],
            'video_url': obj['video_url'],
            'sequence': obj['sequence'],
            'reviewer': obj['reviewer'],
            'unread': obj['unread']
        }
    return comments, 200


# returns all unread comments
@app.get('/comment/unread')
def get_unread_comments():
    comments = {}
    db_records = Comment.objects(unread=True)
    for record in db_records:
        obj = record.json()
        comments[obj['uuid']] = {
            'comment': obj['comment'],
            'date_modified': obj['date_modified'],
            'image_url': obj['image_url'],
            'video_url': obj['video_url'],
            'sequence': obj['sequence'],
            'reviewer': obj['reviewer'],
            'unread': obj['unread']
        }
    return comments, 200


# returns all comments in a given sequence
@app.get('/comment/sequence/<sequence_num>')
def get_sequence_comments(sequence_num):
    comments = {}
    db_records = Comment.objects(sequence=sequence_num)
    for record in db_records:
        obj = record.json()
        comments[obj['uuid']] = {
            'comment': obj['comment'],
            'date_modified': obj['date_modified'],
            'image_url': obj['image_url'],
            'video_url': obj['video_url'],
            'reviewer': obj['reviewer'],
            'unread': obj['unread']
        }
    return comments, 200


# returns all comments for a given reviewer
@app.get('/comment/reviewer/<reviewer_name>')
def get_reviewer_comments(reviewer_name):
    comments = {}
    db_records = Comment.objects(reviewer=reviewer_name)
    for record in db_records:
        obj = record.json()
        comments[obj['uuid']] = {
            'comment': obj['comment'],
            'date_modified': obj['date_modified'],
            'image_url': obj['image_url'],
            'video_url': obj['video_url'],
            'sequence': obj['sequence'],
            'unread': obj['unread']
        }
    return comments, 200


# returns one comment
@app.get('/comment/get/<uuid>')
def get_comment(uuid):
    db_record = Comment.objects(uuid=uuid)
    if not db_record:
        return {404: 'No comment with given uuid'}, 404
    return db_record[0].json(), 200


# add a new reviewer to the database
@app.post('/reviewer/add')
def add_reviewer():
    name = request.values.get('name')
    email = request.values.get('email')
    organization = request.values.get('organization')
    phylum = request.values.get('phylum')
    focus = request.values.get('focus')
    if not name or not phylum:
        return {400: 'Missing required values'}, 400
    try:
        reviewer = Reviewer(
            name=name,
            email=email,
            organization=organization,
            phylum=phylum,
            focus=focus
        ).save()
    except NotUniqueError:
        return {409: 'Already a comment record for given uuid'}, 409
    return reviewer.json(), 201


# update a reviewer's information
@app.put('/reviewer/update/<old_name>')
def update_reviewer_info(old_name):
    new_name = request.values.get('new_name')  # if the name didn't change, this will be the same as old_name
    email = request.values.get('email')
    organization = request.values.get('organization')
    phylum = request.values.get('phylum')
    focus = request.values.get('focus')
    try:
        db_record = Reviewer.objects.get(name=old_name)
    except DoesNotExist:
        return {404: 'No reviewer records found with matching name'}, 404
    db_record.update(
        set__name=new_name,
        set__email=email or '',
        set__organization=organization or '',
        set__phylum=phylum or '',
        set__focus=focus or ''
    )
    return Reviewer.objects.get(name=new_name).json(), 200


# delete a reviewer
@app.delete('/reviewer/delete/<name>')
def delete_reviewer(name):
    try:
        db_record = Reviewer.objects.get(name=name)
    except DoesNotExist:
        return {404: 'No comment records matching given uuid'}, 404
    db_record.delete()
    return {200: 'Reviewer deleted'}, 200


# returns all reviewers saved in the database
@app.get('/reviewer/all')
def get_all_reviewers():
    reviewers = []
    db_records = Reviewer.objects()
    for record in db_records:
        reviewers.append(record.json())
    return reviewers, 200


# the link to share with external reviewers
@app.get('/review/<reviewer_name>')
def review(reviewer_name):
    comments = []
    reviewer_name = reviewer_name.replace('-', ' ')
    matched_records = Comment.objects(reviewer=reviewer_name)
    for record in matched_records:
        record = record.json()
        comments.append(record)
        # check if concept on the server is different than what we have saved
        with requests.get(f'http://hurlstor.soest.hawaii.edu:8082/anno/v1/annotations/{record["uuid"]}') as r:
            server_record = r.json()
        if 'concept' not in record.keys() or record['concept'] != server_record['concept']:
            record['concept'] = server_record['concept']
    data = {'comments': comments, 'reviewer': reviewer_name}
    return render_template('external_review.html', data=data), 200


# route to save reviewer's comments, redirects to success page
@app.post('/save-comments')
def save_comments():
    reviewer_name = request.values.get('reviewer')
    count_success = 0
    list_failures = []
    for value in request.values:
        data = {'comment': request.values.get(value)}
        with requests.put(f'{request.url_root}/comment/update/{value}', data=data) as r:
            if r.status_code == 200:
                count_success += 1
            else:
                list_failures.append(value)
    if count_success > 0:
        return redirect(f'success?name={reviewer_name}&count={count_success}')
    else:
        return {500: f'Internal server error - could not update {list_failures}'}, 500


# displays a save success page
@app.get('/success')
def success():
    name = request.args.get('name')
    count = request.args.get('count')
    data = {'name': name, 'count': count}
    return render_template('save_success.html', data=data), 200


@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404
