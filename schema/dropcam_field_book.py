from mongoengine import Document, IntField, StringField, ListField, EmbeddedDocument, EmbeddedDocumentField


class DeploymentData(EmbeddedDocument):
    """ Schema for dropcam deployment data collection """
    deployment_name = StringField(required=True, max_length=30)
    lat = StringField(required=True, max_length=30)
    long = StringField(required=True, max_length=30)
    depth = IntField(required=True)
    bait_type = StringField(required=True, max_length=30)
    deployment_depth = StringField(required=True, max_length=30)

    def json(self):
        return {
            'deployment_name': self.deployment_name,
            'lat': self.lat,
            'long': self.long,
            'depth': self.depth,
            'bait_type': self.bait_type,
            'deployment_depth': self.deployment_depth,
        }


class DropcamFieldBook(Document):
    """ Schema for dropcam expedition field book collection """
    expedition_name = StringField(required=True, max_length=30)
    deployments = ListField(EmbeddedDocumentField(DeploymentData))

    def json(self):
        return {
            'expedition_name': self.expedition_name,
            'deployments': [deployment.json() for deployment in self.deployments],
        }
