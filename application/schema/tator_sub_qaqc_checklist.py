from mongoengine import Document, IntField, StringField


class TatorSubQaqcChecklist(Document):
    """ Schema for Tator sub QAQC checklist collection """
    transect_media_ids = StringField(required=True, max_length=750)
    names_accepted = IntField(required=True, min_value=0, max_value=2)
    missing_qualifier = IntField(required=True, min_value=0, max_value=2)
    stet_reason = IntField(required=True, min_value=0, max_value=2)
    tentative_id = IntField(required=True, min_value=0, max_value=2)
    missing_upon = IntField(required=True, min_value=0, max_value=2)
    upon_not_substrate = IntField(required=True, min_value=0, max_value=2)
    suspicious_host = IntField(required=True, min_value=0, max_value=2)
    time_diff_host_upon = IntField(required=True, min_value=0, max_value=2)
    missing_ancillary = IntField(required=True, min_value=0, max_value=2)
    notes_remarks = IntField(required=True, min_value=0, max_value=2)
    re_examined = IntField(required=True, min_value=0, max_value=2)
    review_sizes = IntField(required=True, min_value=0, max_value=2)
    unique_taxa = IntField(required=True, min_value=0, max_value=2)
    media_attributes = IntField(required=True, min_value=0, max_value=2)

    def json(self):
        return {
            'names_accepted': self.names_accepted,
            'missing_qualifier': self.missing_qualifier,
            'stet_reason': self.stet_reason,
            'tentative_id': self.tentative_id,
            'missing_upon': self.missing_upon,
            'upon_not_substrate': self.upon_not_substrate,
            'suspicious_host': self.suspicious_host,
            'time_diff_host_upon': self.time_diff_host_upon,
            'missing_ancillary': self.missing_ancillary,
            'notes_remarks': self.notes_remarks,
            're_examined': self.re_examined,
            'review_sizes': self.review_sizes,
            'unique_taxa': self.unique_taxa,
            'media_attributes': self.media_attributes,
        }
