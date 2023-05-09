import json
from datetime import datetime
from flask import render_template, request, redirect, Response
from mongoengine import NotUniqueError, DoesNotExist

from application import app
from comment import Comment


@app.route('/favicon.ico')
def favicon():
    return app.send_static_file('img/favicon.ico')


@app.post('/add_comment')
def add_comment():
    uuid = request.values.get('uuid')
    reviewer = request.values.get('reviewer')
    sequence = request.values.get('sequence')
    if not uuid or not reviewer or not sequence:
        return {400: 'Missing required values'}, 400
    try:
        comment = Comment(uuid=uuid, reviewer=reviewer, sequence=sequence).save()
    except NotUniqueError:
        return {409: 'Already a comment record for given uuid'}, 409
    return comment.json(), 201


@app.put('/update_comment/<uuid>')
def update_comment(uuid):
    try:
        db_record = Comment.objects.get(uuid=uuid)
    except DoesNotExist:
        return {404: 'No comment records matching given uuid'}, 404
    db_record.update(set__comment=request.values.get('comment'), set__date_modified=datetime.now)
    return Comment.objects.get(uuid=uuid).json(), 200


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
        comments.append(record.json())
    # return the rendered template
    return render_template('external_review.html', comments=comments)


@app.post('/save_comments')
def save_comments():
    reviewer_name = request.values.get('reviewer_name')
    time = datetime.now().strftime('%H:%M:%S %b %d %Y')
    comments = {'reviewer': reviewer_name, 'comments': {}}

    for value in request.values:
        comments['comments'][value] = {}
        comments['comments'][value]['text'] = request.values.get(value)
        comments['comments'][value]['time'] = time

    with open(f'comments/{reviewer_name.replace(" ", "_")}.json', 'w') as file:
        json.dump(comments, file)

    reviewer_name = reviewer_name.replace(' ', '%20')
    return redirect(f'success?name={reviewer_name}')


@app.get('/success')
def success():
    name = request.args.get('name')
    return render_template('save_success.html', name=name)


@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404


# check to see if this is the main thread of execution
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8070)
