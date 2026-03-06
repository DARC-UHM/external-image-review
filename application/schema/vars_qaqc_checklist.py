from mongoengine import Document, IntField, StringField


class VarsQaqcChecklist(Document):
    """ Schema for VARS QAQC checklist collection """
    sequence_names = StringField(required=True, max_length=750)
    multiple_associations = IntField(required=True, min_value=0, max_value=2)
    primary_substrate = IntField(required=True, min_value=0, max_value=2)
    identical_s1_s2 = IntField(required=True, min_value=0, max_value=2)
    duplicate_s2 = IntField(required=True, min_value=0, max_value=2)
    upon_substrate = IntField(required=True, min_value=0, max_value=2)
    timestamp_substrate = IntField(required=True, min_value=0, max_value=2)
    missing_upon = IntField(required=True, min_value=0, max_value=2)
    missing_ancillary = IntField(required=True, min_value=0, max_value=2)
    ref_id_concept_name = IntField(required=True, min_value=0, max_value=2)
    ref_id_associations = IntField(required=True, min_value=0, max_value=2)
    blank_associations = IntField(required=True, min_value=0, max_value=2)
    suspicious_host = IntField(required=True, min_value=0, max_value=2)
    expected_association = IntField(required=True, min_value=0, max_value=2)
    time_diff_host_upon = IntField(required=True, min_value=0, max_value=2)
    bounding_boxes = IntField(required=True, min_value=0, max_value=2)
    localizations_missing_bounding_box = IntField(required=True, min_value=0, max_value=2)
    unique_fields = IntField(required=True, min_value=0, max_value=2)

    def json(self):
        return {
            'multiple_associations': self.multiple_associations,
            'primary_substrate': self.primary_substrate,
            'identical_s1_s2': self.identical_s1_s2,
            'duplicate_s2': self.duplicate_s2,
            'upon_substrate': self.upon_substrate,
            'timestamp_substrate': self.timestamp_substrate,
            'missing_upon': self.missing_upon,
            'missing_ancillary': self.missing_ancillary,
            'ref_id_concept_name': self.ref_id_concept_name,
            'ref_id_associations': self.ref_id_associations,
            'blank_associations': self.blank_associations,
            'suspicious_host': self.suspicious_host,
            'expected_association': self.expected_association,
            'time_diff_host_upon': self.time_diff_host_upon,
            'bounding_boxes': self.bounding_boxes,
            'localizations_missing_bounding_box': self.localizations_missing_bounding_box,
            'unique_fields': self.unique_fields,
        }
