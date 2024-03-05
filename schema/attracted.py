from mongoengine import Document, StringField, IntField


class Attracted(Document):
    """ Schema for attracted/unattracted collection """
    scientific_name = StringField(required=True, max_length=100)
    attracted = IntField(required=True, min_value=0, max_value=2)  # 0 = unattracted, 1 = attracted, 2 = both

    def json(self):
        attracted = {
            'scientific_name': self.scientific_name,
            'attracted': self.attracted,
        }
        return attracted
