from mongoengine import Document, StringField, IntField, DateTimeField, BooleanField, ListField, EmbeddedDocument, EmbeddedDocumentField
from datetime import datetime, timedelta


class ReviewerCommentList(EmbeddedDocument):
    """ Schema for list of reviewers and their respective comments """
    reviewer = StringField(required=True, max_length=50)
    comment = StringField(max_length=1000)
    date_modified = DateTimeField(default=(datetime.now() - timedelta(hours=10)))


class Comment(Document):
    """ Schema for comment collection """
    uuid = StringField(unique=True, required=True, max_length=50)
    all_localizations = StringField(max_length=2500)  # for tator comments (JSON string, length allows for about 30 points)
    id_reference = StringField(max_length=100)  # for tator comments
    section_id = IntField()  # for tator comments
    sequence = StringField(required=True, max_length=50)
    timestamp = StringField(max_length=30)
    image_url = StringField(max_length=200)
    reviewer_comments = ListField(EmbeddedDocumentField(ReviewerCommentList))
    annotator = StringField(required=True, max_length=50)
    unread = BooleanField(required=True, default=False)
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
        attributes = ['uuid', 'all_localizations', 'id_reference', 'section_id', 'sequence', 'timestamp',
                      'image_url', 'annotator', 'unread', 'depth', 'lat', 'long', 'temperature',
                      'oxygen_ml_l', 'video_url']
        # create a json object with only the fields that are not None
        comment = {attr: getattr(self, attr) for attr in attributes if getattr(self, attr) is not None}
        comment['reviewer_comments'] = reviewer_comments
        return comment

    meta = {
        'indexes': ['uuid', 'sequence']
    }
