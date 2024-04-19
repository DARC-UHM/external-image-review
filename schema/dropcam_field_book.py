from mongoengine import Document, IntField, FloatField, StringField, ListField, EmbeddedDocument, EmbeddedDocumentField


class DeploymentData(EmbeddedDocument):
    """ Schema for dropcam deployment data collection """
    deployment_name = StringField(required=True, unique=True, max_length=30)
    lat = FloatField(required=True, max_length=30)
    long = FloatField(required=True, max_length=30)
    depth_m = FloatField()
    bait_type = StringField(required=True, max_length=30)

    def json(self):
        return {
            'deployment_name': self.deployment_name,
            'lat': self.lat,
            'long': self.long,
            'depth_m': self.depth_m,
            'bait_type': self.bait_type,
        }


class DropcamFieldBook(Document):
    """ Schema for dropcam expedition field book collection """
    section_id = IntField(required=True, unique=True)
    expedition_name = StringField(required=True, max_length=30)
    deployments = ListField(EmbeddedDocumentField(DeploymentData))

    def json(self):
        return {
            'section_id': self.section_id,
            'expedition_name': self.expedition_name,
            'deployments': [deployment.json() for deployment in self.deployments],
        }
