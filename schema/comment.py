from mongoengine import Document, StringField, DateTimeField, BooleanField, ListField, EmbeddedDocument, EmbeddedDocumentField
from datetime import datetime, timedelta


class ReviewerCommentList(EmbeddedDocument):
    """ Schema for list of reviewers and their respective comments """
    reviewer = StringField(required=True, max_length=50)
    comment = StringField(max_length=1000)
    date_modified = DateTimeField(default=(datetime.now() - timedelta(hours=10)))


class Comment(Document):
    """ Schema for comment collection """

    uuid = StringField(unique=True, required=True, max_length=50)
    scientific_name = StringField(max_length=100)  # for tator comments
    tator_overlay = StringField(max_length=700)  # for tator comments (JSON string, length allows for about 30 points)
    sequence = StringField(required=True, max_length=50)
    timestamp = StringField(max_length=30)
    image_url = StringField(required=True, max_length=200)
    reviewer_comments = ListField(EmbeddedDocumentField(ReviewerCommentList))
    annotator = StringField(required=True, max_length=50)
    unread = BooleanField(required=True)
    depth = StringField(max_length=10)
    lat = StringField(max_length=10)
    long = StringField(max_length=10)
    temperature = StringField(max_length=10)
    oxygen_ml_l = StringField(max_length=10)
    video_url = StringField(max_length=200)

    def json(self):
        reviewer_comments = []
        for reviewer_comment in self.reviewer_comments:
            reviewer_comments.append({
                'reviewer': reviewer_comment.reviewer,
                'comment': reviewer_comment.comment,
                'date_modified': reviewer_comment.date_modified.strftime('%d %b %H:%M HST')
            })
        comment = {
            'uuid': self.uuid,
            'scientific_name': self.scientific_name,
            'tator_overlay': self.tator_overlay,
            'sequence': self.sequence,
            'timestamp': self.timestamp,
            'image_url': self.image_url,
            'reviewer_comments': reviewer_comments,
            'annotator': self.annotator,
            'unread': self.unread,
            'depth': self.depth,
            'lat': self.lat,
            'long': self.long,
            'temperature': self.temperature,
            'oxygen_ml_l': self.oxygen_ml_l,
            'video_url': self.video_url,
        }
        return comment

    meta = {
        'indexes': ['uuid', 'sequence']
    }
