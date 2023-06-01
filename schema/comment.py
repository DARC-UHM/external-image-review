from mongoengine import Document, StringField, DateTimeField, BooleanField
from datetime import datetime, timedelta


class Comment(Document):
    """ Schema for comment collection """

    uuid = StringField(unique=True, required=True, max_length=50)
    sequence = StringField(required=True, max_length=50)
    timestamp = StringField(required=True, max_length=30)
    image_url = StringField(required=True, max_length=200)
    concept = StringField(required=True, max_length=50)
    reviewer = StringField(required=True, max_length=50)
    annotator = StringField(required=True, max_length=50)
    unread = BooleanField(required=True)
    depth = StringField(max_length=10)
    lat = StringField(max_length=10)
    long = StringField(max_length=10)
    video_url = StringField(max_length=200)
    comment = StringField(max_length=1000)
    date_modified = DateTimeField(default=(datetime.now() - timedelta(hours=10)))

    def json(self):
        comment = {
            "uuid": self.uuid,
            "sequence": self.sequence,
            "timestamp": self.timestamp,
            "image_url": self.image_url,
            "concept": self.concept,
            "reviewer": self.reviewer,
            "annotator": self.annotator,
            "unread": self.unread,
            "depth": self.depth,
            "lat": self.lat,
            "long": self.long,
            "video_url": self.video_url,
            "comment": self.comment,
            "date_modified": self.date_modified.strftime('%d %b %H:%M HST')
        }
        return comment

    meta = {
        "indexes": ["uuid", "reviewer", "sequence", "concept"],
        "ordering": ["reviewer", "concept"]
    }
