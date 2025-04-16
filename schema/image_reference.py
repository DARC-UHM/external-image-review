from mongoengine import Document, StringField, ListField


class ImageReference(Document):
    """ Schema for image reference collection """
    scientific_name = StringField(required=True, max_length=100)
    expedition_added = StringField(required=True, max_length=100)
    photos = ListField(StringField(max_length=150), max_length=5, default=[])
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
            'photos': self.photos,
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
