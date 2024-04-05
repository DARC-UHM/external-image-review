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
    unique_fields = IntField(required=True, min_value=0, max_value=2)

    def json(self):
        return {
            'multipleAssociationsCheckbox': self.multiple_associations,
            'primarySubstrateCheckbox': self.primary_substrate,
            'identicalS1S2Checkbox': self.identical_s1_s2,
            'duplicateS2Checkbox': self.duplicate_s2,
            'uponSubstrateCheckbox': self.upon_substrate,
            'timestampSubstrateCheckbox': self.timestamp_substrate,
            'missingUponCheckbox': self.missing_upon,
            'missingAncillaryCheckbox': self.missing_ancillary,
            'refIdConceptNameCheckbox': self.ref_id_concept_name,
            'refIdAssociationsCheckbox': self.ref_id_associations,
            'blankAssociationsCheckbox': self.blank_associations,
            'suspiciousHostCheckbox': self.suspicious_host,
            'expectedAssociationCheckbox': self.expected_association,
            'timeDiffHostUponCheckbox': self.time_diff_host_upon,
            'uniqueFieldsCheckbox': self.unique_fields,
        }
