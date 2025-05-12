from datetime import datetime

from mongoengine import DateTimeField, DecimalField, Document, EmbeddedDocument, EmbeddedDocumentField, IntField, \
    ListField, StringField


class ImageRecord(EmbeddedDocument):
    """ Schema for individual image record (embedded in image reference) """
    tator_elemental_id = StringField(required=True)
    image_name = StringField(max_length=100)
    thumbnail_name = StringField(max_length=100)
    location_short_name = StringField(max_length=100)
    video_url = StringField(max_length=100)
    lat = DecimalField()
    long = DecimalField()
    depth_m = IntField()
    temp_c = DecimalField()
    salinity_m_l = DecimalField()

    KNOWN_LOCATIONS = {
        'FSM': 'Federated States of Micronesia',
        'HAW': 'Hawaii',
        'NIU': 'Niue',
        'PNG': 'Papua New Guinea',
        'PLW': 'Palau',
        'RMI': 'Marshall Islands',
        'SLB': 'Solomon Islands',
    }

    def json(self):
        return {
            'tator_elemental_id': self.tator_elemental_id,
            'image_name': self.image_name,
            'thumbnail_name': self.thumbnail_name,
            'location_short_name': self.location_short_name,
            'location_long_name': self.KNOWN_LOCATIONS.get(self.location_short_name, self.location_short_name),
            'video_url': self.video_url,
            'lat': self.lat,
            'long': self.long,
            'depth_m': self.depth_m,
            'temp_c': self.temp_c,
            'salinity_m_l': self.salinity_m_l,
        }


class ImageReference(Document):
    """ Schema for image reference collection (top-level) """
    created_at = DateTimeField(required=True, default=datetime.now)
    updated_at = DateTimeField(required=True, default=datetime.now)
    scientific_name = StringField(required=True, max_length=100)
    photo_records = ListField(EmbeddedDocumentField(ImageRecord), required=True, max_length=5)
    tentative_id = StringField(max_length=100)
    morphospecies = StringField(max_length=100)
    phylum = StringField(max_length=100)
    class_name = StringField(max_length=100)
    order = StringField(max_length=100)
    family = StringField(max_length=100)
    genus = StringField(max_length=100)
    species = StringField(max_length=100)

    def json(self):
        item = {
            'created_at': self.created_at,
            'updated_at': self.updated_at,
            'scientific_name': self.scientific_name,
            'photo_records': [record.json() for record in self.photo_records],
        }
        for field in [
            'tentative_id',
            'morphospecies',
            'phylum',
            'class_name',
            'order',
            'family',
            'genus',
            'species',
        ]:
            if getattr(self, field):
                item[field] = getattr(self, field)
        return item

    def json_quick(self):
        quick_name = self.scientific_name
        if self.tentative_id:
            quick_name += f'~tid={self.tentative_id}'
        if self.morphospecies:
            quick_name += f'~m={self.morphospecies}'
        return {quick_name: [photo_record.tator_elemental_id for photo_record in self.photo_records]}
