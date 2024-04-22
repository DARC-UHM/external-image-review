import urllib.request
import requests
import os
import dotenv
import sys

DARC_REVIEW_URL = 'https://hurlstor.soest.hawaii.edu:5000'
dotenv.load_dotenv()

"""
{
  media_id: {
    'media_url': str,
    'localizations': [
      {
        '_id': str,
        'frame': int,
      }
    ]
  }
}
"""
media_ids = {}

darc_comments = requests.get(
    f'{DARC_REVIEW_URL}/comment/all',
    headers={
        'API-Key': os.getenv('DARC_REVIEW_API_KEY')
    }
).json()

print(f'Total comments: {len(darc_comments.keys())}')

for uuid, comment in darc_comments.items():
    if 'scientific_name' in comment and comment['scientific_name'] is not None and comment['video_url'] is None:
        localization = requests.get(
            f'https://cloud.tator.io/rest/Localization/{uuid}',
            headers={
                'accept': 'application/json',
                'Authorization': f'Token {os.environ.get("TATOR_TOKEN")}',
            },
        ).json()
        media_id = localization['media']
        if media_id not in media_ids.keys():
            media_res = requests.get(
                f'https://cloud.tator.io/rest/Media/{media_id}?presigned=3600',
                headers={
                    'accept': 'application/json',
                    'Authorization': f'Token {os.environ.get("TATOR_TOKEN")}',
                }
            ).json()
            media_ids[media_id] = {
                'media_url': media_res['media_files']['archival'][0]['path'],
                'localizations': [{'_id': localization['id'], 'frame': localization['frame']}],
            }
        else:
            media_ids[media_id]['localizations'].append({'_id': localization['id'], 'frame': localization['frame']})
        print('.', end='')
        sys.stdout.flush()

print()
print(f'Downloading {len(media_ids.keys())} videos...')
 
for media_id, media_info in media_ids.items():
    # download video
    urllib.request.urlretrieve(
        media_info['media_url'],
        f'{media_id}.mp4'
    )
    # update video_url comment
    for localization in media_info['localizations']:
        comment_res = requests.patch(
            f'{DARC_REVIEW_URL}/comment/video/{localization["_id"]}',
            data={
                'video_url': f'{DARC_REVIEW_URL}/video?link=/tator-video/{media_id}.mp4&time={int(localization["frame"] / 30) - 2}',
            },
            headers={
                'API-Key': os.getenv('DARC_REVIEW_API_KEY'),
            },
        )
    print('.', end='')
    sys.stdout.flush()

print()
print('Done')
