from mongoengine import Document, IntField, StringField


class TatorQaqcChecklist(Document):
    """ Schema for VARS QAQC checklist collection """
    deployment_names = StringField(required=True, max_length=750)
    names_accepted = IntField(required=True, min_value=0, max_value=2)
    missing_qualifier = IntField(required=True, min_value=0, max_value=2)
    stet_reason = IntField(required=True, min_value=0, max_value=2)
    tentative_id = IntField(required=True, min_value=0, max_value=2)
    attracted = IntField(required=True, min_value=0, max_value=2)
    notes_remarks = IntField(required=True, min_value=0, max_value=2)
    unique_taxa = IntField(required=True, min_value=0, max_value=2)
    media_attributes = IntField(required=True, min_value=0, max_value=2)

    def json(self):
        return {
            'names_accepted': self.names_accepted,
            'missing_qualifier': self.missing_qualifier,
            'stet_reason': self.stet_reason,
            'tentative_id': self.tentative_id,
            'attracted': self.attracted,
            'notes_remarks': self.notes_remarks,
            'unique_taxa': self.unique_taxa,
            'media_attributes': self.media_attributes,
        }
