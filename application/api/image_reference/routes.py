import os
from datetime import datetime

import requests
from io import BytesIO
from PIL import Image
from flask import current_app, jsonify, request, send_file
from mongoengine import DoesNotExist

from schema.image_reference import ImageReference
from . import image_reference_bp
from .worms_phylogeny_fetcher import WormsPhylogenyFetcher
from ...require_api_key import require_api_key


# get all image reference items
@image_reference_bp.get('')
def get_image_references():
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
    image_references = ImageReference.objects(**query_filter)
    return jsonify([
        image_ref.json() for image_ref in image_references
    ]), 200


@image_reference_bp.get('/image/<image_name>')
def get_image(image_name):
    file_path = os.path.join(os.getcwd(), current_app.config.get('IMAGE_REF_FOLDER'), image_name)
    if os.path.exists(file_path):
        return send_file(file_path)
    else:
        return jsonify({404: 'Image not found'}), 404


# TODO clean this up and extract to a separate function
@image_reference_bp.post('')
@require_api_key
def add_image_reference():
    """
    Create a new image reference item with one photo record.
    curl -X POST http://localhost:5000/image-reference \
      -d scientific_name="Some Name" \
      -d morphospecies="optional" \
      -d tentative_id="optional" \
      -d lat=10.0 \
      -d long=20.0 \
      -d tator_id=12345
    """
    scientific_name = request.values.get('scientific_name')
    tator_id = request.values.get('tator_id')
    tentative_id = request.values.get('tentative_id')
    morphospecies = request.values.get('morphospecies')
    if not scientific_name or not tator_id:
        return jsonify({400: 'Missing required values'}), 400
    if ImageReference.objects(
        scientific_name=scientific_name,
        tentative_id=tentative_id,
        morphospecies=morphospecies,
    ):
        return jsonify({409: 'Record already exists'}), 409
    current_app.logger.info(f'Adding new image reference: scientific_name={scientific_name}, '
                            f'morphospecies={morphospecies}, tentative_id={tentative_id}')
    # get localization info from tator
    localization_res = requests.get(
        url=f'{current_app.config.get("TATOR_URL")}/rest/Localization/{tator_id}',
        headers={'Authorization': f'Token {os.environ.get("TATOR_TOKEN")}'},
    )
    if localization_res.status_code != 200:
        current_app.logger.error(f'Error retrieving localization info from Tator: {localization_res.text}')
        return jsonify({400: 'Error retrieving localization info from Tator'}), 400
    localization = localization_res.json()
    depth_m = localization['attributes'].get('Depth')
    temp_c = localization['attributes'].get('DO Temperature (celsius)')
    salinity_m_l = localization['attributes'].get('DO Concentration Salin Comp (mol per L)')
    media_id = localization['media']
    frame = localization['frame']
    frame_res = requests.get(
        url=f'{current_app.config.get("TATOR_URL")}/rest/GetFrame/{media_id}?frames={frame}',
        headers={
            'Authorization': f'Token {os.environ.get("TATOR_TOKEN")}',
            'accept': 'image/*',
        },
    )
    if frame_res.status_code != 200:
        current_app.logger.error(f'Error retrieving frame from Tator: {frame_res.text}')
        return jsonify({400: 'Error retrieving frame info from Tator'}), 400
    img = Image.open(BytesIO(frame_res.content))
    image_name = f'{tator_id}.jpg'
    thumbnail_name = f'{tator_id}_thumbnail.jpg'
    image_path = os.path.join(current_app.config.get('IMAGE_REF_FOLDER'), image_name)
    thumbnail_path = os.path.join(current_app.config.get('IMAGE_REF_FOLDER'), thumbnail_name)
    if localization['type'] == 48:  # 48 is BOX, crop the image
        normalized_top_left_x = localization['x']
        normalized_top_left_y = localization['y']
        normalized_width = localization['width']
        normalized_height = localization['height']
        # convert to pixel coordinates
        width = img.width
        height = img.height
        left = int(normalized_top_left_x * width)
        upper = int(normalized_top_left_y * height)
        right = int((normalized_top_left_x + normalized_width) * width)
        lower = int((normalized_top_left_y + normalized_height) * height)
        aspect_ratio = (right - left) / (lower - upper)
        # if aspect ratio is not 16:9, expand the crop box to fit
        if aspect_ratio < 16 / 9:
            # expand the width
            current_width = right - left
            new_width = (lower - upper) * 16 / 9
            left -= (new_width - current_width) // 2
            right += (new_width - current_width) // 2
        elif aspect_ratio > 16 / 9:
            # expand the height
            current_height = lower - upper
            new_height = (right - left) * 9 / 16
            upper -= (new_height - current_height) // 2
            lower += (new_height - current_height) // 2
        # check if the crop box is within the image bounds
        if left < 0:
            right += abs(left)
            left = 0
        if upper < 0:
            lower += abs(upper)
            upper = 0
        if right > width:
            left -= right - width
            right = width
        if lower > height:
            upper -= lower - height
            lower = height
        img = img.crop((left, upper, right, lower))
    img.save(image_path)
    img.thumbnail((600, 600))
    img.save(thumbnail_path)
    attr = {
        'scientific_name': scientific_name,
        'photo_records': [{
            'tator_id': tator_id,
            'image_name': image_name,
            'thumbnail_name': thumbnail_name,
            'lat': request.values.get('lat'),
            'long': request.values.get('long'),
            'depth_m': depth_m,
            'temp_c': temp_c,
            'salinity_m_l': salinity_m_l,
        }],
    }
    for field in ['tentative_id', 'morphospecies']:
        if field in request.values and request.values.get(field):
            attr[field] = request.values.get(field)
    worms_fetcher = WormsPhylogenyFetcher(scientific_name)
    worms_fetcher.fetch(current_app.logger)
    for field in [
        'phylum',
        'class_name',
        'order',
        'family',
        'genus',
        'species',
    ]:
        if worms_fetcher.phylogeny.get(field):
            attr[field] = worms_fetcher.phylogeny[field]
    image_ref = ImageReference(**attr).save()
    return jsonify(image_ref.json()), 201


# update an existing image reference item
@image_reference_bp.patch('/<scientific_name>')
@require_api_key
def update_image_reference(scientific_name):
    # query params are the current record values, body params are the new values
    try:
        # this is how unique records are identified
        db_record = ImageReference.objects.get(
            scientific_name=scientific_name,
            morphospecies=request.args.get('morphospecies'),
            tentative_id=request.args.get('tentative_id'),
        )
        for field in [
            'morphospecies',
            'tentative_id',
            'phylum',
            'class_name',
            'order',
            'family',
            'genus',
            'species',
        ]:
            if updated_value := request.values.get(field):
                db_record.update(**{f'set__{field}': updated_value})
            db_record.update(**{f'set__updated_at': datetime.now()})
    except DoesNotExist:
        return jsonify({
            404: f'No record found matching request: '
                 f'scientific_name={scientific_name}, '
                 f'morphospecies={request.args.get("morphospecies")}, '
                 f'tentative_id={request.args.get("tentative_id")}'
        }), 404

    return jsonify(ImageReference.objects.get(
        scientific_name=scientific_name,
        morphospecies=request.values.get('morphospecies') or request.args.get('morphospecies'),
        tentative_id=request.values.get('tentative_id') or request.args.get('tentative_id'),
    ).json()), 200


# # add a photo record
# @image_reference_bp.post('/<scientific_name>')
# @require_api_key
# def create_photo_record(scientific_name):
#     current_app.logger.info(f'Adding new photo record, request values: {request.values}')
#     tator_id = request.values.get('tator_id')
#     if not tator_id:
#         return jsonify({400: 'Missing required values'}), 400
#     try:
#         db_record = ImageReference.objects.get(
#             scientific_name=scientific_name,
#             morphospecies=request.args.get('morphospecies'),
#             tentative_id=request.args.get('tentative_id'),
#         )
#         for record in db_record.photo_records:
#             if record.tator_id == int(tator_id):
#                 return jsonify({409: 'Photo record already exists'}), 409
#         if len(db_record.photo_records) >= 5:
#             return jsonify({400: 'Can\'t add more than five photo records'}), 400
#         db_record.update(push__photo_records={
#             'tator_id': tator_id,
#             'lat': request.values.get('lat'),
#             'long': request.values.get('long'),
#             'depth_m': request.values.get('depth_m'),
#             'temp_c': request.values.get('temp_c'),
#             'salinity_m_l': request.values.get('salinity_m_l'),
#         })
#     except DoesNotExist:
#         return jsonify({
#             404: f'No record found matching request: '
#                  f'scientific_name={scientific_name}, '
#                  f'morphospecies={request.args.get("morphospecies")}, '
#                  f'tentative_id={request.args.get("tentative_id")}'
#         }), 404
#     return jsonify(ImageReference.objects.get(
#         scientific_name=scientific_name,
#         morphospecies=request.args.get('morphospecies'),
#         tentative_id=request.args.get('tentative_id'),
#     ).json()), 201
#
#
# # update a photo record
# @image_reference_bp.patch('/<scientific_name>/<tator_id>')
# @require_api_key
# def update_photo_record(scientific_name, tator_id):
#     try:
#         db_record = ImageReference.objects.get(
#             scientific_name=scientific_name,
#             morphospecies=request.args.get('morphospecies'),
#             tentative_id=request.args.get('tentative_id'),
#         )
#         # find the photo record to update
#         photo_record = next(
#             (record for record in db_record.photo_records if record.tator_id == int(tator_id)), None
#         )
#         for field in [
#             'lat',
#             'long',
#             'depth_m',
#             'temp_c',
#             'salinity_m_l',
#         ]:
#             if updated_value := request.values.get(field):
#                 photo_record.update(**{f'set__{field}': updated_value})
#     except DoesNotExist:
#         return jsonify({
#             404: f'No record found matching request: '
#                  f'scientific_name={scientific_name}, '
#                  f'morphospecies={request.args.get("morphospecies")}, '
#                  f'tentative_id={request.args.get("tentative_id")}'
#         }), 404
#
#     return jsonify(ImageReference.objects.get(
#         scientific_name=scientific_name,
#         morphospecies=request.values.get('morphospecies') or request.args.get('morphospecies'),
#         tentative_id=request.values.get('tentative_id') or request.args.get('tentative_id'),
#     ).json()), 200


# delete an image reference item
@image_reference_bp.delete('/<scientific_name>')
@require_api_key
def delete_image_reference(scientific_name):
    try:
        db_record = ImageReference.objects.get(
            scientific_name=scientific_name,
            morphospecies=request.args.get('morphospecies'),
            tentative_id=request.args.get('tentative_id'),
        )
        db_record.delete()
    except DoesNotExist:
        return jsonify({
            404: f'No record found matching request: '
                 f'scientific_name={scientific_name}, '
                 f'morphospecies={request.args.get("morphospecies")}, '
                 f'tentative_id={request.args.get("tentative_id")}'
        }), 404
    return jsonify({200: 'Record deleted'}), 200
