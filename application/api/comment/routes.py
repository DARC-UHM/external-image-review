import json
from datetime import datetime, timedelta

from flask import request, jsonify, current_app
from flask_cors import cross_origin
from mongoengine import NotUniqueError, DoesNotExist

from application.require_api_key import require_api_key
from schema.comment import Comment, ReviewerCommentList
from . import comment_bp


# get a single comment item
@comment_bp.get('/get/<uuid>')
@cross_origin()
def get_comment(uuid):
    db_record = Comment.objects(uuid=uuid)
    if not db_record:
        return jsonify({404: 'No comment with given uuid'}), 404
    return jsonify(db_record[0].json()), 200


# get all comments saved in the database
@comment_bp.get('/all')
@require_api_key
def get_all_comments():
    comments = {}
    db_records = Comment.objects()
    for record in db_records:
        obj = record.json()
        comments[obj['uuid']] = record.json()
    return jsonify(comments), 200


# get all unread comments
@comment_bp.get('/unread')
@require_api_key
def get_unread_comments():
    comments = {}
    db_records = Comment.objects(unread=True)
    for record in db_records:
        obj = record.json()
        comments[obj['uuid']] = record.json()
    return jsonify(comments), 200


# get all read comments
@comment_bp.get('/read')
@require_api_key
def get_read_comments():
    comments = {}
    # get comments with unread=False and each reviewer_comment.comment != ''
    db_records = Comment.objects(unread=False, reviewer_comments__comment__ne='')
    for record in db_records:
        obj = record.json()
        comments[obj['uuid']] = record.json()
    return jsonify(comments), 200


# get all comments in a given sequence
@comment_bp.get('/sequence/<sequence_num>')
@require_api_key
def get_sequence_comments(sequence_num):
    comments = {}
    db_records = Comment.objects(sequence=sequence_num)
    for record in db_records:
        obj = record.json()
        comments[obj['uuid']] = record.json()
    return jsonify(comments), 200


# get comments for a given reviewer
@comment_bp.get('/reviewer/<reviewer_name>')
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


# create a new comment item
@comment_bp.post('')
@require_api_key
def add_comment():
    comment = {}
    reviewers = json.loads(request.values.get('reviewers'))
    keys = [
        'uuid',
        'all_localizations',
        'sequence',
        'timestamp',
        'image_url',
        'video_url',
        'annotator',
        'section_id',
    ]
    for key in keys:
        value = request.values.get(key)
        if value is not None and value != '':
            comment[key] = value
    if comment.get('uuid') is None \
            or comment.get('sequence') is None \
            or comment.get('annotator') is None \
            or reviewers is None:
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
    current_app.logger.info(f'New comment added for {", ".join(reviewers)} ({comment["sequence"]}, annotator {comment["annotator"]})')
    return jsonify(comment.json()), 201


# update a reviewer's comment given the reviewer and an observation uuid
@comment_bp.patch('/<reviewer>/<uuid>')
@require_api_key
def update_comment(reviewer, uuid):
    try:
        db_record = Comment.objects.get(uuid=uuid)
    except DoesNotExist:
        return jsonify({404: 'No comment records matching given uuid'}), 404
    for reviewer_comment in db_record.reviewer_comments:
        if reviewer_comment['reviewer'] == reviewer:
            if reviewer_comment['comment'] != request.values.get('comment') \
                    or reviewer_comment['id_consensus'] != request.values.get('idConsensus'):
                reviewer_comment['comment'] = request.values.get('comment')
                reviewer_comment['id_consensus'] = request.values.get('idConsensus')
                reviewer_comment['id_at_time_of_response'] = request.values.get('tentativeId')
                reviewer_comment['date_modified'] = (datetime.now() - timedelta(hours=10))
                db_record.unread = True
                db_record.save()
                return jsonify(Comment.objects.get(uuid=uuid).json()), 200
            return jsonify({304: 'No updates made'}), 304
    return jsonify({404: 'No comment records matching given reviewer'}), 404


# update a comment's reviewers given an observation uuid
@comment_bp.put('/reviewers/<uuid>')
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
@comment_bp.put('/mark-read/<uuid>')
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
@comment_bp.put('/mark-unread/<uuid>')
def mark_comment_unread(uuid):
    try:
        db_record = Comment.objects.get(uuid=uuid)
    except DoesNotExist:
        return jsonify({404: 'No comment records matching given uuid'}), 404
    db_record.update(
        unread=True,
    )
    return jsonify(Comment.objects.get(uuid=uuid).json()), 200


# update a comment's video url
@comment_bp.put('/video-url/<uuid>')
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


# delete a comment given an observation uuid
@comment_bp.delete('/<uuid>')
@require_api_key
def delete_comment(uuid):
    try:
        db_record = Comment.objects.get(uuid=uuid)
    except DoesNotExist:
        return jsonify({404: 'No comment records matching given uuid'}), 404
    db_record.delete()
    return jsonify({200: 'Comment deleted'}), 200
