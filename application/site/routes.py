import base64
import json
import os
import threading
from datetime import datetime
from json import JSONDecodeError

import requests
from flask import request, current_app, render_template, Response, redirect, jsonify
from flask_mail import Message, Mail

from schema.annotator import Annotator
from schema.comment import Comment
from . import site_bp
from .fetch_tator_localization import fetch_tator_localizations
from .fetch_vars_annotation import fetch_vars_annotation


# the link to share with external reviewers
@site_bp.get('/review/<reviewer_name>')
def review(reviewer_name):
    req_time = datetime.now()
    current_app.logger.info(f'Access {reviewer_name}\'s review page - IP Address: {request.remote_addr}')
    current_app.logger.info(request.url)
    return_all_comments = request.args.get('all') == 'true'
    reviewer_name = reviewer_name.replace('-', ' ')
    matched_records = Comment.objects(reviewer_comments__reviewer=reviewer_name).order_by('sequence')
    # we can only get one annotation per VARS API call (but responses are much faster than Tator)
    vars_annotations = []  # using a list: each api call will get passed the object in the list and update it in place
    # we can get many localizations in one Tator API call
    tator_localizations = {}  # using a dict: we'll iterate through the api response with all the localizations and
    tator_elemental_ids = []  #               update each object in the dict using the elemental id as the key
    for record in matched_records:
        record = record.json()
        if return_all_comments or next((x for x in record['reviewer_comments'] if x['reviewer'] == reviewer_name))['comment'] == '':
            # show all comments or only return records that the reviewer has not yet commented on
            if request.args.getlist('annotator') and record['annotator'] not in request.args.getlist('annotator'):
                # filter by annotator if specified
                continue
            if request.args.get('sequence') and request.args.get('sequence') not in record['sequence']:
                # filter by sequence (aka dive/deployment) if specified
                continue
            if record.get('all_localizations') is None or record['all_localizations'] == '':
                vars_annotations.append(record)
            else:
                tator_localizations[record['uuid']] = record
                tator_elemental_ids.append(record['uuid'])
    tator_threads = []
    for i in range(0, len(tator_elemental_ids), 50):  # fetch 50 localizations per API call
        thread = threading.Thread(
            target=fetch_tator_localizations,
            kwargs={
                'elemental_ids': tator_elemental_ids[i:i + 50],
                'tator_localizations': tator_localizations,
                'url_root': request.url_root,
                'tator_url': current_app.config.get('TATOR_URL'),
                'logger': current_app.logger,
            }
        )
        tator_threads.append(thread)
        thread.start()
    for thread in tator_threads:
        thread.join()
    for i in range(0, len(vars_annotations), 30):  # allocate 30 threads at a time to make VARS API calls
        var_threads = []
        for record in vars_annotations[i:i + 30]:
            thread = threading.Thread(
                target=fetch_vars_annotation,
                kwargs={
                    'record_ptr': record,
                    'hurlstor_url': current_app.config.get('HURLSTOR_URL'),
                    'logger': current_app.logger,
                }
            )
            var_threads.append(thread)
            thread.start()
        for thread in var_threads:
            thread.join()
    current_app.logger.info(f'Load time: {datetime.now() - req_time}')
    return render_template('external_review.html', data={
        'comments': [*vars_annotations, *tator_localizations.values()],
        'reviewer': reviewer_name,
    }), 200


# route to save reviewer's comments, redirects to success page
@site_bp.post('/save-comments')
def save_comments():
    def send_email(msg):
        with current_app.app_context():
            mail = Mail(current_app)
            mail.send(msg)

    def formatted_comma_list(items: list) -> str:
        sorted_list = sorted(items)
        if len(sorted_list) == 1:
            return sorted_list[0]
        if len(sorted_list) == 2:
            return f'{sorted_list[0]} and {sorted_list[1]}'
        return f'{", ".join(list(sorted_list)[:-1])}, and {list(sorted_list)[-1]}'

    reviewer_name = request.values.get('reviewer')
    comments = json.loads(request.values.get('comments'))
    sequences = json.loads(request.values.get('sequences'))
    annotators = json.loads(request.values.get('annotators'))
    annotator_emails = [current_app.config.get('ADMIN_EMAIL')]
    count_success = 0
    list_failures = []
    current_app.logger.info(f'{reviewer_name} saving comments')

    for annotator in Annotator.objects():
        annotator_emails.append(annotator.email)  # just add all annotators to the email list
    for comment in comments:
        res = requests.patch(
            f'{request.url_root}/comment/{reviewer_name}/{comment["uuid"]}',
            headers={'API-Key': current_app.config.get('API_KEY')},
            data={'comment': comment["comment"]},
        )
        if res.status_code == 200:
            count_success += 1
        elif res.status_code == 304:
            pass
        else:
            list_failures.append(comment['uuid'])
    if count_success > 0:
        msg = Message(
            f'DARC Review - New Comments from {reviewer_name}',
            sender=current_app.config.get('MAIL_USERNAME'),
            recipients=annotator_emails,
        )
        msg.body = 'Aloha,\n\n' + \
                   f'{reviewer_name} added comments to {count_success} annotation{"s" if count_success > 1 else ""} ' + \
                   f'from {formatted_comma_list(sequences)} (annotator{"s" if len(annotators) > 1 else ""}: {formatted_comma_list(annotators)}).\n\n' + \
                   f'There are now {Comment.objects(unread=True).count()} total unread comments in the external review database.\n\n' + \
                   'DARC Review\n'
        email_thread = threading.Thread(target=send_email, args=(msg,))
        email_thread.start()
        return redirect(f'success?name={reviewer_name}&count={count_success}')
    if list_failures:
        current_app.logger.error(f'Failed to update comments for {list_failures}')
        return jsonify({500: f'Internal server error - could not update {list_failures}'}), 500
    return redirect(f'success?name={reviewer_name}&count={count_success}')


# save success page
@site_bp.get('/success')
def success():
    return render_template('save_success.html', data={
        'name': request.args.get('name'),
        'count': request.args.get('count'),
    }), 200


@site_bp.get('/video')
def video():
    current_app.logger.info(f'Viewed video {request.args.get("link")}')
    return render_template('video.html', data={
        'link': request.args.get('link'),
        'time': request.args.get('time'),
    }), 200


@site_bp.get('/tator-frame/<media_id>/<frame_number>')
def tator_frame(media_id, frame_number):
    url = f'{current_app.config.get("TATOR_URL")}/rest/GetFrame/{media_id}?frames={frame_number}'
    if request.values.get('preview'):
        url += '&quality=650'
    res = requests.get(
        url=url,
        headers={'Authorization': f'Token {os.environ.get("TATOR_TOKEN")}'}
    )
    if res.status_code == 200:
        base64_image = base64.b64encode(res.content).decode('utf-8')
        return Response(base64.b64decode(base64_image), content_type='image/png'), 200
    return '', 500


@site_bp.get('/tator-video/<media_id>')
def tator_video(media_id):
    req = requests.get(
        url=f'https://cloud.tator.io/rest/Media/{media_id}?presigned=3600',
        headers={
            'accept': 'application/json',
            'Authorization': f'Token {os.environ.get("TATOR_TOKEN")}',
        }
    )
    try:
        media = req.json()
    except JSONDecodeError:
        return jsonify({404: 'No media found'}), 404
    user_agent = request.user_agent.string.lower()
    if 'chrome' in user_agent or 'edge' in user_agent or 'safari' in user_agent:
        current_app.logger.info('Playing HEVC')
        return redirect(media['media_files']['archival'][0]['path'])
    current_app.logger.info('Playing AV1')
    return redirect(media['media_files']['streaming'][-1]['path'])


@site_bp.get('/summary/vars/<sequence_num>')
def summary(sequence_num):
    return render_template('vars_summary.html', sequence_num=sequence_num), 200
