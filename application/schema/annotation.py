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

    meta = {
        'indexes': [
            'scientific_name',
            'phylum',
            'survey_type',
            'expedition_name',
            'location',
        ]
    }
