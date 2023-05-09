import datetime
from flask import render_template, request, redirect
from mongoengine import NotUniqueError

from application import app
from comment import Comment


@app.route('/favicon.ico')
def favicon():
    return app.send_static_file('img/favicon.ico')


@app.get('/add_record')
def add_record():
    uuid = request.args.get('uuid')
    reviewer = request.args.get('reviewer')
    try:
        Comment(uuid=uuid, reviewer=reviewer).save()
    except NotUniqueError:
        print('Not added - already a record with this uuid')
        return '500'
    return render_template('view_all.html', data='test')

# in internal image review, load the comment database in the beginning and then add comment section if uuid matches a key


@app.put('/update_record')
def update_record():
    pass


@app.delete('/delete_record')
def delete_record():
    pass


@app.get('/view_all_comments')
def view_all_comments():
    comments = []
    db_records = Comment.objects()
    for record in db_records:
        comments.append({
            'reviewer': record.reviewer,
            'comment': record.comment
        })
    return render_template('view_all.html', data=comments)


@app.get('/review/<reviewer_name>')
def review(reviewer_name):
    comments = []
    matched_records = Comment.objects(reviewer=reviewer_name)
    for record in matched_records:
        comments.append({
            'reviewer': record.reviewer,
            'comment': record.comment
        })

    data = {'annotations': comments, 'reviewer': reviewer_name.title(), 'comments': comments}
    # return the rendered template
    return render_template('external_review.html', data=data)


@app.post('/save_comments')
def save_comments():
    reviewer_name = request.values.get('reviewer_name')
    time = datetime.datetime.now().strftime('%H:%M:%S %b %d %Y')
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
