from mongoengine import Document, StringField


class Annotator(Document):
    """ Schema for annotator collection """
    name = StringField(required=True, max_length=100)
    email = StringField(max_length=100)

    def json(self):
        annotator = {
            'name': self.name,
            'email': self.email,
        }
        return annotator
