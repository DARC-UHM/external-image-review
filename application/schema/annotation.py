import datetime

from mongoengine import Document, StringField, IntField, DateTimeField, URLField, PointField


class Annotation(Document):
    """ Single observation event """
    annotation_id = StringField(unique=True, required=True, max_length=50)
    annotation_platform = StringField(required=True, choices=['VARS', 'Tator'])
    expedition_name = StringField(required=True, max_length=50)
    survey_type = StringField(required=True, choices=['dropcam', 'exploratory', 'transect'])
    observation_timestamp = DateTimeField()
    scientific_name = StringField(required=True)
    phylum = StringField(required=True, max_length=50)
    class_name = StringField(max_length=50)
    order = StringField(max_length=50)
    count = IntField()
    image_url = URLField()
    location = PointField(required=True)
    depth_m = IntField()

    @property
    def lat(self):
        return self.location["coordinates"][1]

    @property
    def lng(self):
        return self.location["coordinates"][0]

    def json(self):
        attributes = [
            'annotation_id',
            'annotation_platform',
            'expedition_name',
            'survey_type',
            'scientific_name',
            'phylum',
            'class_name',
            'order',
            'count',
            'image_url',
            'depth_m'
        ]
        # create a json object with only the fields that are not None
        annotation = {
            attr: getattr(self, attr)
            for attr in attributes if getattr(self, attr) is not None
        }
        if getattr(self, 'observation_timestamp'):
            annotation['observation_timestamp'] = datetime.datetime.isoformat(self.observation_timestamp)
        if self.location:
            annotation['lat'] = self.lat
            annotation['lng'] = self.lng
        return annotation

    meta = {
        'indexes': [
            'scientific_name',
            'phylum',
            'survey_type',
            'expedition_name',
            'location',
        ]
    }
