import logging
from typing import Dict

import requests


class WormsPhylogenyFetcher:
    """
    Fetches phylogenetic data from the WoRMS database.
    """

    WORMS_REST_URL = 'https://www.marinespecies.org/rest'

    def __init__(self, scientific_name: str):
        self.scientific_name = scientific_name
        self.phylogeny = {}

    def fetch(self, logger: logging.Logger):
        """
        Fetches the phylogeny of a given scientific name from WoRMS.
        """
        logger.info(f'Fetching WoRMS phylogeny for {self.scientific_name}')
        worms_id_res = requests.get(url=f'{self.WORMS_REST_URL}/AphiaIDByName/{self.scientific_name}?marine_only=true')
        if worms_id_res.status_code == 200 and worms_id_res.json() != -999:  # -999 means more than one matching record
            logger.info('Only one record found!')
            self.set_phylogeny(worms_id_res.json(), logger)
        else:
            worms_name_res = requests.get(url=f'{self.WORMS_REST_URL}/AphiaRecordsByName/{self.scientific_name}?like=false&marine_only=true&offset=1')
            logger.info(f'Multiple records found: {worms_name_res.json()}')
            if worms_name_res.status_code == 200 and len(worms_name_res.json()) > 0:
                for i, record in enumerate(worms_name_res.json()):
                    if record['status'] == 'accepted':  # just take the first accepted record
                        logger.info(f'Using record at index {i}')
                        self.set_phylogeny(record['AphiaID'], logger)
                        break
            else:
                logger.error(f'No records found for {self.scientific_name}')

    def set_phylogeny(self, aphia_id, logger):
        worms_tree_res = requests.get(url=f'{self.WORMS_REST_URL}/AphiaClassificationByAphiaID/{aphia_id}')
        if worms_tree_res.status_code == 200:
            self.phylogeny = self.flatten_taxa_tree(worms_tree_res.json(), {})
            logger.info(f'Phylogeny populated: {self.phylogeny}')
        else:
            logger.error(f'No phylogeny found for {self.scientific_name}')

    def flatten_taxa_tree(self, tree: Dict, flat: Dict):
        """
        Recursive function taking a taxonomy tree returned from WoRMS API and flattening it into a single dictionary.

        :param Dict tree: The nested taxon tree from WoRMS.
        :param Dict flat: The newly created flat taxon tree.
        """
        rank = tree['rank'].lower()
        if rank == 'class':
            rank = 'class_name'
        flat[rank] = tree['scientificname']
        if tree['child'] is not None:
            self.flatten_taxa_tree(tree['child'], flat)
        return flat
