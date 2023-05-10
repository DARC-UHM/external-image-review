import requests


def get_association(annotation, link_name):
    """ Obtains an association value from the annotation data structure """
    for association in annotation['associations']:
        if association['link_name'] == link_name:
            return association
    return None


class CommentLoader:

    def __init__(self, sequences: list, base_url: str):
        self.sequences = sequences
        self.comments = []  # a list of all the comments we find
        self.base_url = base_url
        for sequence in sequences:
            self.find_comments(sequence)
        self.load_comments()

    def find_comments(self, sequence: str):
        with requests.get(f'http://hurlstor.soest.hawaii.edu:8086/query/dive/{sequence.replace(" ", "%20")}') as r:
            response = r.json()

        video_sequence_name = response['media'][0]['video_sequence_name']

        # Find all records that have comments
        for annotation in response['annotations']:
            comment = get_association(annotation, 'comment')
            if comment:
                # get reviewer name
                comment = comment['link_value'].split(' ')
                print(comment)
                reviewer = []
                for word in comment:
                    if len(word) > 0 and word[0].isupper() and word != 'Sent':
                        reviewer.append(word)
                reviewer = ' '.join(reviewer)

                # get image reference url
                img_url = annotation['image_references'][0]['url']
                for i in range(1, len(annotation['image_references'])):
                    if '.png' in annotation['image_references'][i]['url']:
                        url = annotation['image_references'][i]['url']
                        break
                img_url = img_url.replace('http://hurlstor.soest.hawaii.edu/imagearchive', 'https://hurlimage.soest.hawaii.edu')

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
                    'concept': annotation['concept'],
                    'image_reference': img_url,
                    'sequence': video_sequence_name,
                    'reviewer': reviewer,
                    'id_certainty': id_certainty,
                    'id_reference': id_reference,
                    'upon': upon,
                    'timestamp': annotation['recorded_timestamp']
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
