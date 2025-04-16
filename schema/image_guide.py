from mongoengine import Document, StringField, IntField, ListField


class ImageGuide(Document):
    """ Schema for image guide collection """
    scientific_name = StringField(required=True, max_length=100)
    tentative_id = StringField(max_length=100)
    morphospecies = StringField(max_length=100)
    expedition_added = StringField(max_length=100)
    photos = ListField(StringField(max_length=150), max_length=5, default=[])
    phylum = StringField(max_length=100)
    class_ = StringField(max_length=100)
    order = StringField(max_length=100)
    family = StringField(max_length=100)
    genus = StringField(max_length=100)
    species = StringField(max_length=100)

    def json(self):
        item = {
            'scientific_name': self.scientific_name,
            'photos': self.photos,
        }
        for field in [
            'tentative_id',
            'morphospecies',
            'expedition_added',
            'phylum',
            'class_',
            'order',
            'family',
            'genus',
            'species',
        ]:
            if getattr(self, field):
                item[field] = getattr(self, field)
        return item
