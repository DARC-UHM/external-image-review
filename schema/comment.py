from mongoengine import Document, StringField, IntField, DateTimeField, BooleanField, ListField, EmbeddedDocument, EmbeddedDocumentField
from datetime import datetime, timedelta


class ReviewerCommentList(EmbeddedDocument):
    """ Schema for list of reviewers and their respective comments """
    reviewer = StringField(required=True, max_length=50)
    id_consensus = StringField(choices=['agree', 'disagree', 'uncertain'])
    id_at_time_of_response = StringField(max_length=100)
    comment = StringField(max_length=1500)
    save_for_later = BooleanField()
    date_modified = DateTimeField(default=(datetime.now() - timedelta(hours=10)))


class Comment(Document):
    """ Schema for comment collection """
    uuid = StringField(unique=True, required=True, max_length=50)
    all_localizations = StringField(max_length=2500)  # for tator comments (JSON string, length allows for about 30 points)
    section_id = IntField()  # for tator comments
    sequence = StringField(required=True, max_length=50)
    timestamp = StringField(max_length=30)
    image_url = StringField(max_length=200)
    reviewer_comments = ListField(EmbeddedDocumentField(ReviewerCommentList))
    annotator = StringField(required=True, max_length=50)
    unread = BooleanField(required=True, default=False)
    video_url = StringField(max_length=200)

    def json(self):
        reviewer_comments = []
        for reviewer_comment in self.reviewer_comments:
            comment = {
                'reviewer': reviewer_comment.reviewer,
                'date_modified': reviewer_comment.date_modified.strftime('%d %b %H:%M HST'),
            }
            for field in ['id_consensus', 'id_at_time_of_response', 'comment']:
                if getattr(reviewer_comment, field) is not None:
                    comment[field] = getattr(reviewer_comment, field)
            reviewer_comments.append(comment)
        attributes = [
            'uuid',
            'all_localizations',
            'section_id',
            'sequence',
            'timestamp',
            'image_url',
            'annotator',
            'unread',
            'video_url',
        ]
        # create a json object with only the fields that are not None
        comment = {attr: getattr(self, attr) for attr in attributes if getattr(self, attr) is not None}
        comment['reviewer_comments'] = reviewer_comments
        return comment

    meta = {
        'indexes': ['uuid', 'sequence']
    }
