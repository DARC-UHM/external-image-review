from mongoengine import (Document, StringField, IntField, DateTimeField, BooleanField, ListField,
                         EmbeddedDocument, EmbeddedDocumentField)
from datetime import datetime, timedelta


class ReviewerCommentList(EmbeddedDocument):
    """ Schema for list of reviewers and their respective comments """
    reviewer = StringField(required=True, max_length=50)
    id_consensus = StringField(choices=['agree', 'disagree', 'uncertain'])
    id_at_time_of_response = StringField(max_length=100)
    comment = StringField(max_length=1500)
    favorite = BooleanField()
    date_modified = DateTimeField(default=(datetime.now() - timedelta(hours=10)))

    def json(self):
        comment = {
            'reviewer': self.reviewer,
            'favorite': self.favorite,
            'date_modified': self.date_modified.strftime('%d %b %Y %H:%M HST'),
        }
        for field in ['id_consensus', 'id_at_time_of_response', 'comment']:
            if getattr(self, field) is not None:
                comment[field] = getattr(self, field)
        return comment


class Taxonomy(EmbeddedDocument):
    """ Schema for taxonomy information of a comment, used for filtering & sorting comments by taxonomy """
    phylum = StringField(required=True, max_length=50)
    tax_class = StringField(max_length=50)
    order = StringField(max_length=50)
    family = StringField(max_length=50)
    genus = StringField(max_length=50)
    species = StringField(max_length=50)

    def json(self):
        taxonomy = {'phylum': self.phylum}
        if getattr(self, 'tax_class') is not None:
            taxonomy['class'] = getattr(self, 'tax_class')
        for field in ['order', 'family', 'genus', 'species']:
            if getattr(self, field) is not None:
                taxonomy[field] = getattr(self, field)
        return taxonomy


class Comment(Document):
    """ Schema for comment collection """
    uuid = StringField(unique=True, required=True, max_length=50)
    all_localizations = StringField(max_length=2500)  # for tator comments (JSON string, length allows for about 30 points)
    section_id = IntField()  # for tator comments
    sequence = StringField(required=True, max_length=50)
    timestamp = StringField(max_length=30)
    image_url = StringField(max_length=200)
    reviewer_comments = ListField(EmbeddedDocumentField(ReviewerCommentList))
    taxonomy = EmbeddedDocumentField(Taxonomy)
    phylum = StringField(max_length=50)  # todo delete
    annotator = StringField(required=True, max_length=50)
    unread = BooleanField(required=True, default=False)
    video_url = StringField(max_length=200)

    def json(self):
        attributes = [
            'uuid',
            'all_localizations',
            'phylum',
            'section_id',
            'sequence',
            'timestamp',
            'image_url',
            'annotator',
            'unread',
            'video_url',
        ]
        # create a json object with only the fields that are not None
        comment = {
            attr: getattr(self, attr)
            for attr in attributes if getattr(self, attr) is not None
        }
        comment['reviewer_comments'] = [
            reviewer_comment.json() for reviewer_comment in self.reviewer_comments
        ]
        if self.taxonomy is not None:
            comment['taxonomy'] = self.taxonomy.json()
        return comment

    meta = {
        'indexes': ['uuid', 'sequence', 'unread', 'reviewer_comments.reviewer']
    }
