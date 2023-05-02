import requests
import pandas as pd

from util.translate_substrate import translate_substrate_code


def get_association(annotation, link_name):
    """ Obtains an association value from the annotation data structure """
    for association in annotation['associations']:
        if association['link_name'] == link_name:
            return association
    return None


class ReviewImageLoader:

    def __init__(self, sequence_names: list, reviewer_names: list):
        self.distilled_records = []
        self.reviewer_names = reviewer_names  # one or more reviewers
        for name in sequence_names:
            self.load_images(name)

    def load_images(self, name: str):
        concept_phylogeny = {}
        image_records = []

        with requests.get(f'http://hurlstor.soest.hawaii.edu:8086/query/dive/{name.replace(" ", "%20")}') as r:
            response = r.json()

        video_sequence_name = response['media'][0]['video_sequence_name']

        """ 
        Get all of the animal annotations that have images
        """
        for annotation in response['annotations']:
            concept_name = annotation['concept']
            if annotation['image_references'] and concept_name[0].isupper():
                match_name = False
                for association in annotation['associations']:
                    if association['link_name'] == 'comment':
                        for name in self.reviewer_names:
                            if name in association['link_value']:
                                match_name = True
                                break
                if match_name:
                    image_records.append(annotation)
                    if concept_name not in concept_phylogeny.keys():
                        # get the phylogeny from VARS kb
                        concept_phylogeny[concept_name] = {}
                        with requests.get(f'http://hurlstor.soest.hawaii.edu:8083/kb/v1/phylogeny/up/{concept_name}') \
                                as vars_tax_res:
                            if vars_tax_res.status_code == 200:
                                # this get us to phylum
                                vars_tree = \
                                    vars_tax_res.json()['children'][0]['children'][0]['children'][0]['children'][0]['children'][0]
                                while 'children' in vars_tree.keys():
                                    if 'rank' in vars_tree.keys():  # sometimes it's not
                                        concept_phylogeny[concept_name][vars_tree['rank']] = vars_tree['name']
                                    vars_tree = vars_tree['children'][0]
                                if 'rank' in vars_tree.keys():
                                    concept_phylogeny[concept_name][vars_tree['rank']] = vars_tree['name']
                            else:
                                print(f'Unable to find record for {annotation["concept"]}')

        """
        Define dataframe for sorting data
        """
        annotation_df = pd.DataFrame(columns=[
            'observation_uuid',
            'concept',
            'identity-certainty',
            'identity-reference',
            'guide-photo',
            'comment',
            'image_url',
            'upon',
            'recorded_timestamp',
            'video_sequence_name',
            'phylum',
            'subphylum',
            'superclass',
            'class',
            'subclass',
            'superorder',
            'order',
            'suborder',
            'infraorder',
            'superfamily',
            'family',
            'subfamily',
            'genus',
            'species'
        ])

        # add the records to the dataframe
        for record in image_records:
            # convert hyphens to underlines and remove excess data
            observation_uuid = record['observation_uuid']
            concept_name = record['concept']
            guide_photo = None
            id_cert = None
            id_ref = None
            upon = None
            comment = None
            phylum = None
            subphylum = None
            superclass = None
            class_ = None
            subclass = None
            superorder = None
            order = None
            suborder = None
            infraorder = None
            superfamily = None
            family = None
            subfamily = None
            genus = None
            species = None

            temp = get_association(record, 'identity-certainty')
            if temp:
                id_cert = temp['link_value']

            temp = get_association(record, 'identity-reference')
            if temp:
                id_ref = temp['link_value']

            temp = get_association(record, 'guide-photo')
            if temp:
                guide_photo = temp['to_concept']

            temp = get_association(record, 'upon')
            if temp:
                upon = translate_substrate_code(temp['to_concept'])

            temp = get_association(record, 'comment')
            if temp:
                comment = temp['link_value']

            if 'phylum' in concept_phylogeny[concept_name].keys():
                phylum = concept_phylogeny[concept_name]['phylum']
            if 'subphylum' in concept_phylogeny[concept_name].keys():
                subphylum = concept_phylogeny[concept_name]['subphylum']
            if 'superclass' in concept_phylogeny[concept_name].keys():
                superclass = concept_phylogeny[concept_name]['superclass']
            if 'class' in concept_phylogeny[concept_name].keys():
                class_ = concept_phylogeny[concept_name]['class']
            if 'subclass' in concept_phylogeny[concept_name].keys():
                subclass = concept_phylogeny[concept_name]['subclass']
            if 'superorder' in concept_phylogeny[concept_name].keys():
                superorder = concept_phylogeny[concept_name]['superorder']
            if 'order' in concept_phylogeny[concept_name].keys():
                order = concept_phylogeny[concept_name]['order']
            if 'suborder' in concept_phylogeny[concept_name].keys():
                suborder = concept_phylogeny[concept_name]['suborder']
            if 'infraorder' in concept_phylogeny[concept_name].keys():
                infraorder = concept_phylogeny[concept_name]['infraorder']
            if 'superfamily' in concept_phylogeny[concept_name].keys():
                superfamily = concept_phylogeny[concept_name]['superfamily']
            if 'family' in concept_phylogeny[concept_name].keys():
                family = concept_phylogeny[concept_name]['family']
            if 'subfamily' in concept_phylogeny[concept_name].keys():
                subfamily = concept_phylogeny[concept_name]['subfamily']
            if 'genus' in concept_phylogeny[concept_name].keys():
                genus = concept_phylogeny[concept_name]['genus']
            if 'species' in concept_phylogeny[concept_name].keys():
                species = concept_phylogeny[concept_name]['species']

            url = record['image_references'][0]['url']

            for i in range(1, len(record['image_references'])):
                if '.png' in record['image_references'][i]['url']:
                    url = record['image_references'][i]['url']
                    break

            url = url.replace('http://hurlstor.soest.hawaii.edu/imagearchive', 'https://hurlimage.soest.hawaii.edu')

            temp_df = pd.DataFrame([[
                observation_uuid,
                concept_name,
                id_cert,
                id_ref,
                guide_photo,
                comment,
                url,
                upon,
                record['recorded_timestamp'],
                video_sequence_name,
                phylum,
                subphylum,
                superclass,
                class_,
                subclass,
                superorder,
                order,
                suborder,
                infraorder,
                superfamily,
                family,
                subfamily,
                genus,
                species
            ]], columns=[
                'observation_uuid',
                'concept',
                'identity-certainty',
                'identity-reference',
                'guide-photo',
                'comment',
                'image_url',
                'upon',
                'recorded_timestamp',
                'video_sequence_name',
                'phylum',
                'subphylum',
                'superclass',
                'class',
                'subclass',
                'superorder',
                'order',
                'suborder',
                'infraorder',
                'superfamily',
                'family',
                'subfamily',
                'genus',
                'species'
            ])

            annotation_df = pd.concat([annotation_df, temp_df], ignore_index=True)

        annotation_df = annotation_df.sort_values(by=[
            'phylum',
            'subphylum',
            'superclass',
            'class',
            'subclass',
            'superorder',
            'order',
            'suborder',
            'infraorder',
            'superfamily',
            'family',
            'subfamily',
            'genus',
            'species',
            'concept',
            'identity-reference',
            'identity-certainty',
            'recorded_timestamp'
        ])

        for index, row in annotation_df.iterrows():
            self.distilled_records.append({
                'observation_uuid': row['observation_uuid'],
                'concept': row['concept'],
                'identity_certainty': row['identity-certainty'],
                'identity_reference': row['identity-reference'],
                'guide_photo': row['guide-photo'],
                'comment': row['comment'],
                'image_url': row['image_url'],
                'upon': row['upon'],
                'recorded_timestamp': row['recorded_timestamp'],
                'video_sequence_name': row['video_sequence_name']
            })
