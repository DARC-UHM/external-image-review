import re

from flask import current_app, jsonify, request

from schema.comment import Comment
from . import stats_bp
from ...vars_summary import VarsSummary


@stats_bp.get('/stats/vars/<sequence_num>')
def sequence_stats(sequence_num):
    current_app.logger.info(f'Got stats for VARS: {sequence_num} - IP Address: {request.remote_addr}')
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
