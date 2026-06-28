import base64
import os
import threading

import requests
from flask import request, current_app, render_template, Response, redirect, jsonify, stream_with_context

from application.schema.comment import Comment
from application.schema.reviewer import Reviewer
from . import site_bp
from .fetch_tator_localization import fetch_tator_localizations
from .fetch_vars_annotation import fetch_vars_annotation
from .slack_helper import SlackHelper
from ..get_request_ip import get_request_ip
from ..schema.annotation import Annotation
from ..schema.image_reference import ImageReference


# the link to share with external reviewers
@site_bp.get('/review/<reviewer_name>')
def review(reviewer_name):
    current_app.logger.info(f'Access {reviewer_name}\'s review page - IP Address: {get_request_ip()}')
    current_app.logger.info(request.url)
    reviewer_name = reviewer_name.replace('-', ' ')
    return_all_comments = request.args.get('all') == 'true'
    annotators_filter = request.args.getlist('annotator')
    phylum_filter = request.args.getlist('phylum')
    class_filter = request.args.getlist('class')
    order_filter = request.args.getlist('order')
    family_filter = request.args.getlist('family')
    genus_filter = request.args.getlist('genus')
    sequence_filter = request.args.get('sequence')

    query = Comment.objects(reviewer_comments__reviewer=reviewer_name)

    if annotators_filter:
        query = query.filter(annotator__in=annotators_filter)
    if phylum_filter:
        query = query.filter(taxonomy__phylum__in=phylum_filter)
    if class_filter:
        query = query.filter(taxonomy__tax_class__in=class_filter)
    if order_filter:
        query = query.filter(taxonomy__order__in=order_filter)
    if family_filter:
        query = query.filter(taxonomy__family__in=family_filter)
    if genus_filter:
        query = query.filter(taxonomy__genus__in=genus_filter)
    if sequence_filter:
        query = query.filter(sequence__icontains=sequence_filter)

    # we can only get one annotation per VARS API call (but responses are much faster than Tator)
    vars_annotations = []  # using a list: each api call will get passed the object in the list and update it in place
    # we can get many localizations in one Tator API call
    tator_localizations = {}  # using a dict: we'll iterate through the api response with all the localizations and
    tator_elemental_ids = []  #               update each object in the dict using the elemental id as the key

    for comment in query:
        record = comment.json()
        reviewer_comment = next((x for x in record['reviewer_comments'] if x['reviewer'] == reviewer_name))
        # records need review if "all" flag is set or reviewer has not yet commented
        no_response = not reviewer_comment.get('id_consensus') and not reviewer_comment.get('comment')
        needs_review = return_all_comments or no_response
        if not needs_review:
            continue
        if not record.get('all_localizations'):
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

    comments = sorted([*vars_annotations, *tator_localizations.values()], key=lambda x: (
        x.get('taxonomy', {}).get('phylum') or 'ZZZZ',
        x.get('taxonomy', {}).get('class') or 'ZZZZ',
        x.get('taxonomy', {}).get('order') or 'ZZZZ',
        x.get('taxonomy', {}).get('family') or 'ZZZZ',
        x.get('taxonomy', {}).get('genus') or 'ZZZZ',
        x.get('taxonomy', {}).get('species') or 'ZZZZ',
    ))

    return render_template('external_review.html', data={
        'comments': comments,
        'reviewer': reviewer_name,
    }), 200


# save one card of reviewer comments
@site_bp.post('/save-comments')
def save_comments():
    current_app.logger.info(f'Saving reviewer comments: {request.json}')
    uuids = request.json.get('uuids')
    reviewer = request.json.get('reviewer')
    annotator = request.json.get('annotator')
    sequence = request.json.get('sequence')
    if uuids is None or len(uuids) == 0:
        return jsonify({'error': 'At least one uuid is required'}), 400
    if reviewer is None or reviewer == '':
        return jsonify({'error': 'Reviewer is required'}), 400
    if annotator is None or annotator == '':
        return jsonify({'error': 'Annotator is required'}), 400
    if sequence is None or sequence == '':
        return jsonify({'error': 'Sequence is required'}), 400
    count_updated = 0
    count_sames = 0
    count_failed = 0
    for uuid in uuids:
        res = requests.patch(
            url=f'{request.url_root}/comment/{uuid}',
            json={
                'reviewer': reviewer,
                'comment': request.json.get('comment'),
                'id_consensus': request.json.get('idConsensus'),
                'tentative_id': request.json.get('tentativeId'),
            },
        )
        if res.status_code == 200:
            count_updated += 1
        elif res.status_code == 304:
            current_app.logger.info(f'No updates made for reviewer comment for {uuid}')
            count_sames += 1
        else:
            current_app.logger.error(f'Failed to save reviewer comment for {uuid}: {res.text}')
            count_failed += 1
    current_app.logger.info(f"count updated: {count_updated}, count same: {count_sames}, count failed: {count_failed}")
    if count_updated > 0:
        SlackHelper(
            reviewer=reviewer,
            sequence=sequence,
            annotator=annotator,
            logger=current_app.logger,
            slack_client=current_app.config.get('SLACK_CLIENT'),
            slack_channel_id=current_app.config.get('SLACK_CHANNEL_ID'),
        ).send_message()
        return jsonify({'message': 'Comments saved'}), 200
    if count_sames > 0:
        return jsonify({'message': 'No updates made'}), 304
    return jsonify({'error': 'Error saving comments'}), 500


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
    if request.values.get('thumbnail'):
        url += '&quality=300'
    elif request.values.get('preview'):
        url += '&quality=650'
    res = requests.get(
        url=url,
        headers={'Authorization': f'Token {os.environ.get("TATOR_TOKEN")}'}
    )
    if res.status_code == 200:
        base64_image = base64.b64encode(res.content).decode('utf-8')
        return Response(base64.b64decode(base64_image), content_type='image/png'), 200
    return '', 500


# view tator localization image (cropped)
@site_bp.get('/tator-localization-image/<localization_id>')
def tator_image(localization_id):
    res = requests.get(
        url=f'{current_app.config.get("TATOR_URL")}/rest/LocalizationGraphic/{localization_id}',
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
    if req.status_code != 200:
        current_app.logger.error(f'Failed to fetch media info for media id {media_id} from Tator API: {req.text}')
        return jsonify({'error': 'Tator API error', 'status': req.status_code}), 502
    try:
        media = req.json()
    except ValueError:
        current_app.logger.exception("Failed to parse JSON from Tator API")
        return jsonify({'error': 'Invalid JSON from upstream'}), 502
    user_agent = request.user_agent.string.lower()
    if 'archival' in media['media_files'].keys() and ('chrome' in user_agent or 'edge' in user_agent or 'safari' in user_agent):
        current_app.logger.info('Playing HEVC')
        return redirect(media['media_files']['archival'][0]['path'])
    current_app.logger.info('Playing AV1')
    best_stream = max(
        media['media_files']['streaming'],
        key=lambda s: s['resolution'][0]
    )
    media_res = requests.get(best_stream['path'], stream=True)
    return Response(
        stream_with_context(media_res.iter_content(chunk_size=1024 * 512)),
        content_type="video/mp4",
        headers={
            "Accept-Ranges": "bytes"
        }
    )


@site_bp.get('/summary/vars/<sequence_num>')
def summary(sequence_num):
    return render_template('vars_summary.html', sequence_num=sequence_num), 200


@site_bp.get('/image-references')
def image_reference_page():
    current_app.logger.info(f'Access image references page - IP Address: {get_request_ip()}')
    query_filter = {}
    if phylum := request.args.get('phylum'):
        query_filter['phylum'] = phylum
    if class_name := request.args.get('class'):
        query_filter['class_name'] = class_name
    if order := request.args.get('order'):
        query_filter['order'] = order
    if family := request.args.get('family'):
        query_filter['family'] = family
    if genus := request.args.get('genus'):
        query_filter['genus'] = genus
    if species := request.args.get('species'):
        query_filter['species'] = species
    image_references = ImageReference.objects(**query_filter).order_by(
        'phylum',
        'class_name',
        'order',
        'family',
        'genus',
        'species',
        'scientific_name',
        'tentative_id',
    )
    return render_template('image-reference.html', image_references=[image_ref.json() for image_ref in image_references])


# observations map
@site_bp.get('/observations')
def animal_page():
    name_filter = request.values.get('name')
    phylum_filter = request.values.get('phylum')
    class_filter = request.values.get('class')
    order_filter = request.values.get('order')
    expedition_filter = request.values.get('expedition')
    survey_type_filter = request.values.get('survey-type')

    query = Annotation.objects()

    if expedition_filter:
        query = query.filter(expedition_name=expedition_filter)
    if survey_type_filter:
        query = query.filter(survey_type=survey_type_filter)
    if name_filter:
        query = query.filter(scientific_name=name_filter)
    if phylum_filter:
        query = query.filter(phylum=phylum_filter)
    if class_filter:
        query = query.filter(class_name=class_filter)
    if order_filter:
        query = query.filter(order=order_filter)

    current_app.logger.info(f'Access observations page - IP Address: {get_request_ip()}')
    current_app.logger.info(request.url)

    return render_template('observations.html', annotations=[annotation.json() for annotation in query])
