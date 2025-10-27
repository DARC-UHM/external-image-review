from mongoengine import Document, StringField, EmbeddedDocument, IntField, ListField, DateTimeField, \
    EmbeddedDocumentField


class SlackMessage(EmbeddedDocument):
    count = IntField()
    annotators = ListField(StringField())
    dives = ListField(StringField())
    scheduled_message_id = StringField()
    scheduled_time = DateTimeField()


class Reviewer(Document):
    """ Schema for reviewer collection """
    name = StringField(required=True, unique=True, max_length=100)
    email = StringField(max_length=100)
    organization = StringField(max_length=150)
    phylum = StringField(required=True, max_length=150)
    focus = StringField(max_length=150)
    slack_message = EmbeddedDocumentField(SlackMessage)

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
