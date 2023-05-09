import json
from mongoengine import Document, StringField, DateTimeField
from datetime import datetime


class Comment(Document):
    uuid = StringField(unique=True, required=True)
    sequence = StringField(required=True)
    reviewer = StringField(required=True)
    comment = StringField(max_length=1000)
    date_modified = DateTimeField(default=datetime.now)

    def json(self):
        comment = {
            "uuid": self.uuid,
            "sequence": self.sequence,
            "reviewer": self.reviewer,
            "comment": self.comment,
            "date_modified": self.date_modified.isoformat()
        }
        return comment

    meta = {
        "indexes": ["uuid", "reviewer", "sequence"],
        "ordering": ["reviewer"]
    }
