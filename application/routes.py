import datetime
import os

from flask import render_template, request, redirect

from application import app


@app.route('/favicon.ico')
def favicon():
    return app.send_static_file('img/favicon.ico')


@app.get('/view_all_comments')
def view_all_comments():
    # get list of sequences
    with open('sequences.json', 'r') as jsonSeq:
        sequences = json.load(jsonSeq)
    comments = {}
    reviewers = []
    for filename in os.listdir('comments'):
        with open(f'comments/{filename}', 'r') as f:
            data = json.load(f)
            comments = data['comments'] | comments  # merge dicts
            reviewers.append(data['reviewer'])
    records = []
    if len(reviewers) > 0:
        image_loader = ReviewImageLoader(sequences, reviewers)
        records = image_loader.distilled_records
    data = {'annotations': records, 'comments': comments}
    return render_template('view_all.html', data=data)


@app.get('/review/<reviewer_name>')
def review(reviewer_name):
    # get list of sequences
    with open('sequences.json', 'r') as jsonSeq:
        sequences = json.load(jsonSeq)
    # get images in sequence
    image_loader = ReviewImageLoader(sequences, [reviewer_name])
    comments = {}

    # get saved comments
    try:
        with open(f'comments/{reviewer_name.replace(" ", "_")}.json', 'r') as file:
            comments = json.load(file)['comments']
            print('Loaded saved comments')
    except FileNotFoundError:
        print('No saved comments')

    data = {'annotations': image_loader.distilled_records, 'reviewer': reviewer_name.title(), 'comments': comments}
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
