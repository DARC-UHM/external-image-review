import json
import webbrowser
import requests
from flask import Flask, render_template, request, redirect
from jinja2 import Environment, FileSystemLoader

from review_image_loader import ReviewImageLoader

# initialize a flask object
app = Flask(__name__)
env = Environment(loader=FileSystemLoader('templates/'))
images = env.get_template('external_review.html')
sequence_update = env.get_template('sequence_update.html')
save_success = env.get_template('save_success.html')
err404 = env.get_template('404.html')


@app.route('/favicon.ico')
def favicon():
    return app.send_static_file('img/favicon.ico')


@app.get('/review/<reviewer_name>')
def review(reviewer_name):
    # get list of sequences
    with open('sequences.json', 'r') as jsonSeq:
        sequences = json.load(jsonSeq)
    # get images in sequence
    image_loader = ReviewImageLoader(sequences, reviewer_name)
    comments = {}

    # get saved comments
    try:
        with open(f'comments/{reviewer_name.replace(" ", "_")}.comments', 'r') as file:
            comments = json.load(file)
            print('Loaded saved comments')
    except FileNotFoundError:
        print('No saved comments')

    data = {'annotations': image_loader.distilled_records, 'reviewer': reviewer_name.title(), 'comments': comments}
    # return the rendered template
    return render_template(images, data=data)


@app.get('/view_sequences')
def view_sequences():
    pass


@app.get('/update_sequences')
def update_sequences_get():
    # get list of sequences
    with open('sequences.json', 'r') as jsonSeq:
        sequences = json.load(jsonSeq)
    # get list of sequences from vars
    with requests.get('http://hurlstor.soest.hawaii.edu:8084/vam/v1/videosequences/names') as r:
        video_sequences = r.json()

    return render_template(sequence_update, all_sequences=video_sequences, sequences=sequences)


@app.post('/update_sequences')
def update_sequences_post():
    updated_sequences = []
    for key, val in request.values.items():
        updated_sequences.append(val)
    with open('sequences.json', 'w') as file:
        json.dump(updated_sequences, file)
    return {"hehe": "hoho"}


@app.post('/save_comments')
def save_comments():
    reviewer_name = request.values.get('reviewer_name')
    comments = {'reviewer_name': reviewer_name}

    for value in request.values:
        comments[value] = request.values.get(value)

    with open(f'comments/{reviewer_name.replace(" ", "_")}.comments', 'w') as file:
        json.dump(comments, file)

    reviewer_name = reviewer_name.replace(' ', '%20')
    return redirect(f'success?name={reviewer_name}')


@app.get('/success')
def success():
    name = request.args.get('name')
    return render_template(save_success, name=name)


@app.errorhandler(404)
def page_not_found(e):
    return render_template(err404), 404


def open_browser():
    webbrowser.open_new('http://127.0.0.1:5000')


# check to see if this is the main thread of execution
if __name__ == '__main__':
    # Timer(1, open_browser).start()
    app.run(host='0.0.0.0', port=8070)
