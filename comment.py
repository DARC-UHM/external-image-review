from mongoengine import Document, StringField, DateTimeField
from datetime import datetime


class Comment(Document):
    uuid = StringField(unique=True, required=True, max_length=50)
    sequence = StringField(required=True, max_length=100)
    timestamp = StringField(required=True, max_length=30)
    image_reference = StringField(required=True, max_length=200)
    concept = StringField(required=True, max_length=100)
    reviewer = StringField(required=True, max_length=100)
    video_url = StringField(max_length=200)
    id_certainty = StringField(max_length=50)
    id_reference = StringField(max_length=3)
    upon = StringField(max_length=100)
    comment = StringField(max_length=1000)
    date_modified = DateTimeField(default=datetime.now)

    def json(self):
        comment = {
            "uuid": self.uuid,
            "sequence": self.sequence,
            "timestamp": self.timestamp,
            "image_reference": self.image_reference,
            "concept": self.concept,
            "reviewer": self.reviewer,
            "video_url": self.video_url,
            "id_certainty": self.id_certainty,
            "id_reference": self.id_reference,
            "upon": self.upon,
            "comment": self.comment,
            "date_modified": self.date_modified.isoformat()
        }
        return comment

    meta = {
        "indexes": ["uuid", "reviewer", "sequence", "concept"],
        "ordering": ["reviewer", "concept"]
    }
