import csv
import io

from flask import current_app, jsonify, request
from dateutil import parser as dateparser

from . import annotation_bp
from ...require_api_key import require_api_key
from ...schema.annotation import Annotation


def safe_round(val):
    if val is None or val == '':
        return None
    try:
        return round(val)
    except ValueError:
        return None


def safe_float(val):
    if val is None or val == '':
        return None
    try:
        return float(val)
    except ValueError:
        return None


def safe_datetime(val):
    if not val:
        return None
    try:
        return dateparser.parse(val)
    except Exception:
        return None


# upload a finalized summary tsv file from tator
@annotation_bp.post('/load-summary')
@require_api_key
def import_annotations_tsv():
    current_app.logger.info('Importing annotations from tsv file')
    if 'file' not in request.files:
        return jsonify({'error': 'Missing file'}), 400

    file = request.files['file']
    expedition_name = file.filename.split('.')[0]
    survey_type = 'dropcam'

    if 'DOEX0' not in expedition_name:
        return jsonify({'error': 'expedition name must contain DOEX0'}), 400

    if '(' in expedition_name:
        survey_type = expedition_name.split('(')[1].split(')')[0].strip()
        expedition_name = expedition_name.split('(')[0].strip()

    current_app.logger.info(f'Expedition name: {expedition_name}, Survey type: {survey_type}')

    raw = file.stream.read().decode('utf-8')
    reader = csv.DictReader(io.StringIO(raw), delimiter='\t')

    created = 0
    skipped = 0
    errors = []

    for i, row in enumerate(reader):
        try:
            annotation_id = row.get('tatorId') or f'row_{i}'

            # prevent duplicates
            if Annotation.objects(annotation_id=annotation_id).first():
                print(f'Skipping duplicate annotation_id {annotation_id}')
                skipped += 1
                continue

            lat = safe_float(row.get('latitude'))
            lng = safe_float(row.get('longitude'))

            if lat is None or lng is None:
                print(f'Skipping row {i} due to missing lat/lng')
                skipped += 1
                continue

            annotation = Annotation(
                annotation_id=annotation_id,
                annotation_platform='Tator',
                expedition_name=expedition_name,
                survey_type=survey_type,
                observation_timestamp=safe_datetime(row.get('observationTimestamp')),
                scientific_name=row.get('scientificName'),
                phylum=row.get('phylum'),
                class_name=row.get('class'),
                order=row.get('order'),
                count=row.get('individualCount'),
                image_url=row.get('publicImageUrl'),
                location={
                    'type': 'Point',
                    'coordinates': [lng, lat]
                },
                depth_m=safe_round(safe_float(row.get('depth(m)')))
            )

            annotation.save()
            created += 1

        except Exception as e:
            errors.append({'row': i, 'error': str(e)})

    current_app.logger.info(f'Import completed: {created} created, {skipped} skipped, {len(errors)} errors')

    return jsonify({
        'created': created,
        'skipped': skipped,
        'errors': errors[:20]
    })
