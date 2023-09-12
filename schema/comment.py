from mongoengine import Document, StringField, DateTimeField, BooleanField, DictField
from datetime import datetime, timedelta


class Comment(Document):
    """ Schema for comment collection """

    uuid = StringField(unique=True, required=True, max_length=50)
    sequence = StringField(required=True, max_length=50)
    timestamp = StringField(required=True, max_length=30)
    image_url = StringField(required=True, max_length=200)
    concept = StringField(max_length=50)
    reviewer_comments = DictField(required=True)
    annotator = StringField(required=True, max_length=50)
    unread = BooleanField(required=True)
    depth = StringField(max_length=10)
    lat = StringField(max_length=10)
    long = StringField(max_length=10)
    video_url = StringField(max_length=200)
    id_reference = StringField(max_length=20)  # dive num + id ref to account for duplicate numbers across dives
    date_modified = DateTimeField(default=(datetime.now() - timedelta(hours=10)))

    def json(self):
        comment = {
            'uuid': self.uuid,
            'sequence': self.sequence,
            'timestamp': self.timestamp,
            'image_url': self.image_url,
            'reviewer_comments': self.reviewer_comments,
            'annotator': self.annotator,
            'unread': self.unread,
            'depth': self.depth,
            'lat': self.lat,
            'long': self.long,
            'video_url': self.video_url,
            'id_reference': self.id_reference,
            'date_modified': self.date_modified.strftime('%d %b %H:%M HST')
        }
        return comment

    meta = {
        'indexes': ['uuid', 'sequence']
    }
