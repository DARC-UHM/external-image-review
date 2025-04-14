import os

from application import app


if __name__ == '__main__':
    if os.environ.get('FLASK_ENV') == 'development':
        app.run(debug=True)
    else:
        app.run(host='0.0.0.0', port=5000)
