import json
import os
import requests

TERM_RED = '\033[1;31;48m'
TERM_YELLOW = '\033[1;93m'
TERM_NORMAL = '\033[1;37;0m'


class VarsSummary:
    def __init__(self, sequence_num: str):
        self.phylogeny = {}
        self.annotators = set()
        self.annotation_count = 0
        self.individual_count = 0
        self.unique_taxa_individuals = {}
        self.video_millis = 0
        self.image_count = 0
        self.phylum_counts = {}
        # get list of sequences from vars
        with requests.get('http://hurlstor.soest.hawaii.edu:8084/vam/v1/videosequences/names') as req:
            self.matched_sequences = [sequence for sequence in req.json() if sequence_num in sequence]

    def load_phylogeny(self):
        try:
            with open(os.path.join('cache', 'phylogeny.json'), 'r') as f:
                self.phylogeny = json.load(f)
        except FileNotFoundError:
            self.phylogeny = {'Animalia': {}}

    def save_phylogeny(self):
        try:
            with open(os.path.join('cache', 'phylogeny.json'), 'w') as f:
                json.dump(self.phylogeny, f, indent=2)
        except FileNotFoundError:
            os.makedirs('cache')
        with open(os.path.join('cache', 'phylogeny.json'), 'w') as f:
            json.dump(self.phylogeny, f, indent=2)

    def fetch_vars_phylogeny(self, concept_name: str, no_match_records: set):
        """
        Fetches phylogeny for given concept from the VARS knowledge base.
        """
        vars_tax_res = requests.get(url=f'http://hurlstor.soest.hawaii.edu:8083/kb/v1/phylogeny/up/{concept_name}')
        if vars_tax_res.status_code == 200:
            try:
                # this get us to phylum
                vars_tree = vars_tax_res.json()['children'][0]['children'][0]['children'][0]['children'][0]['children'][0]
                self.phylogeny[concept_name] = {}
            except KeyError:
                if concept_name not in no_match_records:
                    no_match_records.add(concept_name)
                    print(f'{TERM_YELLOW}WARNING: Could not find phylogeny for concept "{concept_name}" in VARS knowledge base{TERM_NORMAL}')
                vars_tree = {}
            while 'children' in vars_tree.keys():
                if 'rank' in vars_tree.keys():  # sometimes it's not
                    self.phylogeny[concept_name][vars_tree['rank']] = vars_tree['name']
                vars_tree = vars_tree['children'][0]
            if 'rank' in vars_tree.keys():
                self.phylogeny[concept_name][vars_tree['rank']] = vars_tree['name']
        else:
            print(f'\n{TERM_RED}Unable to find record for {concept_name}{TERM_NORMAL}')

    def get_summary(self):
        self.load_phylogeny()
        identity_references = set()
        no_match_records = set()
        for sequence in self.matched_sequences:
            with requests.get(f'http://hurlstor.soest.hawaii.edu:8086/query/dive/{sequence.replace(" ", "%20")}') as r:
                _json = r.json()
                self.annotation_count += len(_json['annotations'])
                for video in _json['media']:
                    if 'image collection' not in video['video_name']:
                        self.video_millis += video['duration_millis']
                for annotation in _json['annotations']:
                    if annotation['concept'][0].islower():  # ignore non-taxonomic concepts
                        continue
                    if len(annotation['image_references']) > 0:
                        self.image_count += 1
                    self.annotators.add(annotation['observer'])
                    id_ref = None
                    cat_abundance = None
                    pop_quantity = None
                    for association in annotation['associations']:
                        if association['link_name'] == 'identity-reference':
                            id_ref = association['link_value']
                        elif association['link_name'] == 'categorical-abundance':
                            cat_abundance = association['link_value']
                        elif association['link_name'] == 'population-quantity':
                            pop_quantity = association['link_value']

                    if id_ref:
                        if id_ref in identity_references:  # we already counted this one
                            continue
                        else:  # add to set so we don't count it again
                            identity_references.add(id_ref)

                    if annotation['concept'] not in self.phylogeny.keys() and annotation['concept'] not in no_match_records:
                        self.fetch_vars_phylogeny(annotation['concept'], no_match_records)

                    this_phylum = self.phylogeny.get(annotation['concept'])
                    if not this_phylum:
                        print(f'{TERM_RED}No phylogeny found for {annotation["concept"]}{TERM_NORMAL}')
                        continue
                    this_phylum = this_phylum.get('phylum', 'Unknown')
                    this_count = 1  # default count if no cat abundance or pop quantity

                    if cat_abundance:
                        match cat_abundance:
                            case '11-20':
                                this_count = 15
                            case '21-50':
                                this_count = 35
                            case '51-100':
                                this_count = 75
                            case '\u003e100':
                                this_count = 100
                    elif pop_quantity and pop_quantity != '':
                        this_count = int(pop_quantity)

                    self.individual_count += this_count
                    self.phylum_counts[this_phylum] = self.phylum_counts.get(this_phylum, 0) + this_count
                    self.unique_taxa_individuals[annotation['concept']] = self.unique_taxa_individuals.get(annotation['concept'], 0) + this_count
        phylum_keys = list(self.phylum_counts.keys())
        self.phylum_counts['Other'] = 0
        for phylum in phylum_keys:
            if self.phylum_counts[phylum] < 100:
                self.phylum_counts['Other'] += self.phylum_counts[phylum]
                del self.phylum_counts[phylum]
        self.save_phylogeny()
        self.annotators.discard('python-script')
