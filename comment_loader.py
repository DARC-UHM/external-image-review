import requests
from datetime import datetime


def get_association(annotation, link_name):
    """ Obtains an association value from the annotation data structure """
    for association in annotation['associations']:
        if association['link_name'] == link_name:
            return association
    return None


def parse_datetime(timestamp: str) -> datetime:
    """
    Returns a datetime object given a timestamp string.

    :param str timestamp: The timestamp to parse.
    :return datetime: The timestamp parsed as a datetime object.
    """
    if '.' in timestamp:
        return datetime.strptime(timestamp, '%Y-%m-%dT%H:%M:%S.%fZ')
    return datetime.strptime(timestamp, '%Y-%m-%dT%H:%M:%SZ')


class CommentLoader:

    def __init__(self, sequences: list, base_url: str):
        self.sequences = sequences
        self.comments = []  # a list of all the comments we find
        self.base_url = base_url
        for sequence in sequences:
            self.find_comments(sequence)
        self.load_comments()

    def find_comments(self, sequence: str):
        videos = []

        with requests.get(f'http://hurlstor.soest.hawaii.edu:8086/query/dive/{sequence.replace(" ", "%20")}') as r:
            response = r.json()

        # get list of video links and start timestamps
        for video in response['media']:
            if 'urn:imagecollection:org' not in video['uri']:
                videos.append([parse_datetime(video['start_timestamp']),
                    video['uri'].replace('http://hurlstor.soest.hawaii.edu/videoarchive', 'https://hurlvideo.soest.hawaii.edu')])

        video_sequence_name = response['media'][0]['video_sequence_name']

        # find all records that have comments
        for annotation in response['annotations']:
            comment = get_association(annotation, 'comment')
            if comment:
                # get reviewer name
                comment = comment['link_value'].split(' ')
                reviewer = []
                for word in comment:
                    if len(word) > 0 and word[0].isupper() and \
                            word.lower() not in ['sent', 'send', 'right', 'left', 'referring', 'outreach/pr']:
                        word = ''.join(char for char in word if char.isalnum())
                        reviewer.append(word)
                reviewer = ' '.join(reviewer)
                if len(reviewer) > 0 and len(annotation['image_references']):
                    # get image reference url
                    img_url = annotation['image_references'][0]['url']
                    for i in range(1, len(annotation['image_references'])):
                        if '.png' in annotation['image_references'][i]['url']:
                            img_url = annotation['image_references'][i]['url']
                            break
                    img_url = img_url.replace('http://hurlstor.soest.hawaii.edu/imagearchive', 'https://hurlimage.soest.hawaii.edu')

                    # get video reference url
                    timestamp = parse_datetime(annotation['recorded_timestamp'])

                    print('anno 1:')
                    print(timestamp.isoformat())

                    video_url = videos[0]
                    for video in videos:
                        print(video[0].isoformat())
                        if video[0] > timestamp:
                            break
                        video_url = video
                    time_diff = timestamp - video_url[0]
                    video_url = f'{video_url[1]}#t={int(time_diff.total_seconds()) - 5}'

                    print('\n')
                    # get optional associations
                    id_certainty = None
                    id_reference = None
                    upon = None

                    temp = get_association(annotation, 'identity-certainty')
                    if temp:
                        id_certainty = temp['link_value']

                    temp = get_association(annotation, 'identity-reference')
                    if temp:
                        id_reference = temp['link_value']

                    temp = get_association(annotation, 'upon')
                    if temp:
                        upon = temp['to_concept']

                    self.comments.append({
                        'uuid': annotation['observation_uuid'],
                        'sequence': video_sequence_name,
                        'timestamp': timestamp,
                        'image_url': img_url,
                        'concept': annotation['concept'],
                        'reviewer': reviewer,
                        'video_url': video_url,
                        'id_certainty': id_certainty,
                        'id_reference': id_reference,
                        'upon': upon
                    })

    def load_comments(self):
        # sends comments to mongodb
        count_success = 0
        count_failure = 0
        for comment in self.comments:
            req = requests.post(f'{self.base_url}/add_comment', data=comment)
            if req.status_code == 201:
                count_success += 1
            else:
                count_failure += 1
        if count_success > 0:
            print(f'Successfully loaded {count_success} comments to database.')
        if count_failure > 0:
            print(f'Failed to load {count_failure} comments')
