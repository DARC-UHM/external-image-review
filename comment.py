import json
from mongoengine import Document, StringField, DateTimeField
from datetime import datetime


class Comment(Document):
    uuid = StringField(unique=True, required=True)
    concept = StringField(required=True)
    image_reference = StringField(required=True)
    id_certainty = StringField(default='-')
    id_reference = StringField(default='-')
    upon = StringField(default='-')
    timestamp = StringField(default='-')
    sequence = StringField(required=True)
    reviewer = StringField(required=True)
    comment = StringField(max_length=1000)
    date_modified = DateTimeField(default=datetime.now)

    def json(self):
        comment = {
            "uuid": self.uuid,
            "concept": self.concept,
            "image_reference": self.image_reference,
            "sequence": self.sequence,
            "id_certainty": self.id_certainty,
            "id_reference": self.id_reference,
            "upon": self.upon,
            "timestamp": self.timestamp,
            "reviewer": self.reviewer,
            "comment": self.comment,
            "date_modified": self.date_modified.isoformat()
        }
        return comment

    meta = {
        "indexes": ["uuid", "reviewer", "sequence", "concept"],
        "ordering": ["reviewer", "concept"]
    }
