import traceback

from flask import render_template, request, jsonify, make_response

from application import app
from application.get_request_ip import get_request_ip
from application.require_api_key import require_api_key
from schema.comment import Comment


@app.route('/favicon.ico')
def favicon():
    return app.send_static_file('img/favicon.ico')


@app.get('/robots.txt')
def robots():
    response = make_response('User-agent: *\nDisallow: /', 200)
    response.mimetype = 'text/plain'
    return response


@app.get('/reset-test-reviewer-comments')
def reset_test_reviewer_comments():
    comments = Comment.objects(reviewer_comments__reviewer="Test Reviewer")
    for db_record in comments:
        for reviewer_comment in db_record.reviewer_comments:
            if reviewer_comment['reviewer'] == "Test Reviewer":
                reviewer_comment['comment'] = ""
                reviewer_comment['id_consensus'] = None
                db_record.save()
    return jsonify({'message': 'Test Reviewer comments reset'}), 200


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


@app.post('/log-error')
def log_error():
    app.logger.error('Error from internal annotation review app:')
    app.logger.error(request.json.get('error'))
    return jsonify({200: 'Error logged'}), 200


@app.errorhandler(404)
def page_not_found(e):
    app.logger.info(f'Tried to access page {request.url} - IP Address: {get_request_ip()}')
    return render_template('404.html'), 404


@app.errorhandler(Exception)
def internal_server_error(e):
    app.logger.error(f'Internal server error - IP Address: {get_request_ip()}')
    app.logger.error(type(e).__name__)
    app.logger.error(e)
    app.logger.error(traceback.format_exc())
    return render_template('500.html'), 500
