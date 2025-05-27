from mongoengine import Document, IntField, StringField


class TatorQaqcChecklist(Document):
    """ Schema for Tator QAQC checklist collection """
    deployment_names = StringField(required=True, max_length=750)
    names_accepted = IntField(required=True, min_value=0, max_value=2)
    missing_qualifier = IntField(required=True, min_value=0, max_value=2)
    stet_reason = IntField(required=True, min_value=0, max_value=2)
    tentative_id = IntField(required=True, min_value=0, max_value=2)
    attracted = IntField(required=True, min_value=0, max_value=2)
    non_target_not_attracted = IntField(required=True, min_value=0, max_value=2)
    exists_in_image_refs = IntField(required=True, min_value=0, max_value=2)
    same_name_qualifier = IntField(required=True, min_value=0, max_value=2)
    notes_remarks = IntField(required=True, min_value=0, max_value=2)
    re_examined = IntField(required=True, min_value=0, max_value=2)
    unique_taxa = IntField(required=True, min_value=0, max_value=2)
    media_attributes = IntField(required=True, min_value=0, max_value=2)

    def json(self):
        return {
            'names_accepted': self.names_accepted,
            'missing_qualifier': self.missing_qualifier,
            'stet_reason': self.stet_reason,
            'tentative_id': self.tentative_id,
            'attracted': self.attracted,
            'non_target_not_attracted': self.non_target_not_attracted,
            'exists_in_image_refs': self.exists_in_image_refs,
            'same_name_qualifier': self.same_name_qualifier,
            'notes_remarks': self.notes_remarks,
            're_examined': self.re_examined,
            'unique_taxa': self.unique_taxa,
            'media_attributes': self.media_attributes,
        }
