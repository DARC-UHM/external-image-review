from mongoengine import Document, StringField, DateTimeField


class Reviewer(Document):
    """ Schema for reviewer collection """
    name = StringField(required=True, max_length=100)
    email = StringField(max_length=100)
    organization = StringField(max_length=150)
    focus_group = StringField(required=True, max_length=150)
    focus_subgroup = StringField(max_length=150)
    last_contacted = DateTimeField()

    def json(self):
        reviewer = {
            "name": self.name,
            "email": self.email,
            "organization": self.organization,
            "focus_group": self.focus_group,
            "focus_subgroup": self.focus_subgroup,
            "last_contacted": self.last_contacted
        }
        return reviewer

    meta = {
        "indexes": ["focus_subgroup", "focus_group"],
        "ordering": ["focus_group"]
    }
