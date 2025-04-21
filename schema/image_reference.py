from mongoengine import DecimalField, Document, EmbeddedDocument, EmbeddedDocumentField, IntField, \
    ListField, StringField


class ImageRecord(EmbeddedDocument):
    tator_id = IntField(required=True)
    lat = DecimalField()
    long = DecimalField()
    depth_m = IntField()
    temp_c = DecimalField()
    salinity_m_l = DecimalField()

    def json(self):
        return {
            'tator_id': self.tator_id,
            'lat': self.lat,
            'long': self.long,
            'depth_m': self.depth_m,
            'temp_c': self.temp_c,
            'salinity_m_l': self.salinity_m_l,
        }


class ImageReference(Document):
    """ Schema for image reference collection """
    scientific_name = StringField(required=True, max_length=100)
    expedition_added = StringField(required=True, max_length=100)
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
            'scientific_name': self.scientific_name,
            'expedition_added': self.expedition_added,
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
