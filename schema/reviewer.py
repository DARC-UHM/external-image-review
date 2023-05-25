from mongoengine import Document, StringField


class Reviewer(Document):
    """ Schema for reviewer collection """
    name = StringField(required=True, max_length=100)
    email = StringField(max_length=100)
    organization = StringField(max_length=150)
    phylum = StringField(required=True, max_length=150)
    focus = StringField(max_length=150)

    def json(self):
        reviewer = {
            'name': self.name,
            'email': self.email,
            'organization': self.organization,
            'phylum': self.phylum,
            'focus': self.focus,
        }
        return reviewer

    meta = {
        'indexes': ['phylum'],
        'ordering': ['phylum', 'name']
    }
