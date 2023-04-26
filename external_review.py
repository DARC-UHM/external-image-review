import json
import webbrowser
from flask import Flask, render_template, request, redirect, url_for
from jinja2 import Environment, FileSystemLoader

from image_loader import ImageLoader
from review_image_loader import ReviewImageLoader
from sequences import sequences

# initialize a flask object
app = Flask(__name__)
env = Environment(loader=FileSystemLoader('templates/'))
home = env.get_template('index.html')
images = env.get_template('external_review.html')
err404 = env.get_template('404.html')


@app.route('/favicon.ico')
def favicon():
    return app.send_static_file('img/favicon.ico')


@app.route('/')
def index():
    # return the rendered template
    return render_template(home)


@app.get('/review/<reviewer_name>')
def review(reviewer_name):
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


@app.post('/save_comments')
def save_comments():
    reviewer_name = request.values.get('reviewer_name')
    comments = {'reviewer_name': reviewer_name}

    for value in request.values:
        comments[value] = request.values.get(value)

    with open(f'comments/{reviewer_name.replace(" ", "_")}.comments', 'w') as file:
        json.dump(comments, file)

    reviewer_name = reviewer_name.replace(' ', '%20')
    return redirect(f'/review/{reviewer_name}')


@app.errorhandler(404)
def page_not_found(e):
    return render_template(err404), 404


def open_browser():
    webbrowser.open_new('http://127.0.0.1:5000')


# check to see if this is the main thread of execution
if __name__ == '__main__':
    # Timer(1, open_browser).start()
    app.run(debug=True)
