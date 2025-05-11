import logging
import os

import requests
from flask import abort
from mongoengine import DoesNotExist
from werkzeug.exceptions import HTTPException

from application.api.image_reference.tator_frame_fetcher import TatorFrameFetcher
from application.api.image_reference.worms_phylogeny_fetcher import WormsPhylogenyFetcher
from schema.dropcam_field_book import DropcamFieldBook
from schema.image_reference import ImageReference


class ImageReferenceSaver:
    def __init__(self, tator_url: str, image_ref_dir_path: str, logger: logging.Logger):
        self.tator_url = tator_url
        self.image_ref_dir_path = image_ref_dir_path
        self.logger = logger
        self.scientific_name = None
        self.morphospecies = None
        self.tentative_id = None
        self.deployment_name = None
        self.section_id = None
        self.tator_localization_id = None
        self.localization_media_id = None
        self.localization_frame = None
        self.localization_type = None
        self.normalized_top_left_x_y = None
        self.normalized_dimensions = None
        self.depth_m = None
        self.temp_c = None
        self.salinity_m_l = None

    def load_from_tator_localization_id(self, localization_id):
        # if lone tator localization id is passed, fetch the rest of the data from tator
        localization_res = requests.get(
            url=f'{self.tator_url}/rest/Localization/{localization_id}',
            headers={
                'Authorization': f'Token {os.environ.get("TATOR_TOKEN")}',
                'Content-Type': 'application/json',
            }
        )
        if localization_res.status_code != 200:
            abort(localization_res.status_code, 'Error fetching localization from Tator')
        localization = localization_res.json()
        self.tator_localization_id = localization_id
        self.scientific_name = localization['attributes'].get('Scientific Name')
        self.tentative_id = localization['attributes'].get('Tentative ID')
        self.morphospecies = localization['attributes'].get('Morphospecies')
        self.localization_media_id = localization['media']
        self.localization_frame = localization['frame']
        self.localization_type = localization['type']
        self.normalized_top_left_x_y = (localization['x'], localization['y'])
        self.normalized_dimensions = (localization['width'], localization['height'])
        self.depth_m = localization['attributes'].get('Depth')
        self.temp_c = localization['attributes'].get('DO Temperature (celsius)')
        self.salinity_m_l = localization['attributes'].get('DO Concentration Salin Comp (mol per L)')
        if self.tentative_id == '':
            self.tentative_id = None
        if self.morphospecies == '':
            self.morphospecies = None
        if self.depth_m:
            self.depth_m = round(self.depth_m)
        if self.temp_c:
            self.temp_c = round(self.temp_c, 2)
        if self.salinity_m_l:
            self.salinity_m_l = round(self.salinity_m_l, 2)
        # still need deployment name and section id, get this from media query
        media_res = requests.get(
            url=f'{self.tator_url}/rest/Media/{self.localization_media_id}',
            headers={
                'Authorization': f'Token {os.environ.get("TATOR_TOKEN")}',
                'Content-Type': 'application/json',
            },
        )
        if media_res.status_code != 200:
            abort(media_res.status_code, 'Error fetching media from Tator')
        media = media_res.json()
        self.deployment_name = '_'.join(media['name'].split('.')[0].split('_')[:-1])
        self.section_id = media['primary_section']

    def load_from_json(self, json_payload):
        self.scientific_name = json_payload.get('scientific_name')
        self.morphospecies = json_payload.get('morphospecies')
        self.tentative_id = json_payload.get('tentative_id')
        self.deployment_name = json_payload.get('deployment_name')
        self.section_id = json_payload.get('section_id')
        self.tator_localization_id = json_payload.get('tator_localization_id')
        self.localization_media_id = json_payload.get('localization_media_id')
        self.localization_frame = json_payload.get('localization_frame')
        self.localization_type = json_payload.get('localization_type')
        self.normalized_top_left_x_y = json_payload.get('normalized_top_left_x_y')
        self.normalized_dimensions = json_payload.get('normalized_dimensions')
        self.depth_m = json_payload.get('depth_m')
        self.temp_c = json_payload.get('temp_c')
        self.salinity_m_l = json_payload.get('salinity_m_l')
        if not self.scientific_name \
                or not self.section_id \
                or not self.deployment_name \
                or not self.tator_localization_id \
                or not self.localization_media_id \
                or not self.localization_frame \
                or not self.localization_type:
            raise ValueError('Missing required fields')

    def save(self) -> dict:
        if db_record := ImageReference.objects(
                scientific_name=self.scientific_name,
                tentative_id=self.tentative_id,
                morphospecies=self.morphospecies,
        ).first():
            return self.add_photo_record(db_record)  # image reference item already exists, add a new photo record
        return self.add_image_reference()  # image reference item does not exist, create a new one

    def add_photo_record(self, db_record) -> dict:
        for record in db_record.photo_records:
            if record.tator_localization_id == int(self.tator_localization_id):
                abort(409, 'Photo record already exists')
        if len(db_record.photo_records) >= 5:
            abort(400, 'Five photo records already exist')
        self.logger.info(f'Adding new photo record for image reference: scientific_name={self.scientific_name}, '
                         f'morphospecies={self.morphospecies}, tentative_id={self.tentative_id}')
        try:
            fetched_data = self.fetch_data_and_save_image()
            video_url = f'https://hurlstor.soest.hawaii.edu:5000/video?link=/tator-video/{self.localization_media_id}&time={round(self.localization_frame / 30)}'
            db_record.update(push__photo_records={
                'tator_localization_id': self.tator_localization_id,
                'image_name': fetched_data['image_name'],
                'thumbnail_name': fetched_data['thumbnail_name'],
                'location_short_name': self.deployment_name.split('_')[0],
                'video_url': video_url,
                'lat': fetched_data['lat'],
                'long': fetched_data['long'],
                'depth_m': self.depth_m or fetched_data['depth_m'],
                'temp_c': self.temp_c,
                'salinity_m_l': self.salinity_m_l,
            })
        except HTTPException as e:
            abort(e.code, e.description)
        return ImageReference.objects.get(
            scientific_name=self.scientific_name,
            morphospecies=self.morphospecies,
            tentative_id=self.tentative_id,
        ).json()

    def add_image_reference(self) -> dict:
        self.logger.info(f'Adding new image reference: scientific_name={self.scientific_name}, '
                         f'morphospecies={self.morphospecies}, tentative_id={self.tentative_id}')
        try:
            fetched_data = self.fetch_data_and_save_image()
        except HTTPException as e:
            abort(e.code, e.description)
        worms_fetcher = WormsPhylogenyFetcher(self.scientific_name)
        worms_fetcher.fetch(self.logger)
        video_url = f'https://hurlstor.soest.hawaii.edu:5000/video?link=/tator-video/{self.localization_media_id}&time={round(self.localization_frame / 30)}'
        attr = {
            'scientific_name': self.scientific_name,
            'photo_records': [{
                'tator_localization_id': self.tator_localization_id,
                'image_name': fetched_data['image_name'],
                'thumbnail_name': fetched_data['thumbnail_name'],
                'video_url': video_url,
                'location_short_name': self.deployment_name.split('_')[0],
                'lat': fetched_data['lat'],
                'long': fetched_data['long'],
                'depth_m': self.depth_m or fetched_data['depth_m'],
                'temp_c': self.temp_c,
                'salinity_m_l': self.salinity_m_l,
            }],
        }
        if self.tentative_id:
            attr['tentative_id'] = self.tentative_id
        if self.morphospecies:
            attr['morphospecies'] = self.morphospecies
        for field in ['phylum', 'class_name', 'order', 'family', 'genus', 'species']:
            if worms_fetcher.phylogeny.get(field):
                attr[field] = worms_fetcher.phylogeny[field]
        image_ref = ImageReference(**attr).save()
        return image_ref.json()

    def fetch_data_and_save_image(self) -> dict:
        # get the lat/long from the field book
        lat = None
        long = None
        depth_m = None
        try:
            dropcam_fieldbook = DropcamFieldBook.objects.get(section_id=self.section_id)
            for deployment in dropcam_fieldbook['deployments']:
                if deployment['deployment_name'] == self.deployment_name:
                    lat = deployment['lat']
                    long = deployment['long']
                    depth_m = deployment['depth_m']
                    break
        except DoesNotExist:
            self.logger.warning(f'No field book found for section {self.section_id}')
        if not lat or not long:
            self.logger.warning(f'No lat/long found for deployment {self.deployment_name}')
        # get the image/ctd data from Tator
        tator_fetcher = TatorFrameFetcher(
            localization_id=self.tator_localization_id,
            localization_media_id=self.localization_media_id,
            localization_frame=self.localization_frame,
            localization_type=self.localization_type,
            normalized_top_left_x_y=self.normalized_top_left_x_y,
            normalized_dimensions=self.normalized_dimensions,
            tator_url=self.tator_url,
            logger=self.logger,
        )
        tator_fetcher.fetch_frame()
        tator_fetcher.save_images(self.image_ref_dir_path)
        return {
            'image_name': tator_fetcher.image_name,
            'thumbnail_name': tator_fetcher.thumbnail_name,
            'lat': lat,
            'long': long,
            'depth_m': depth_m,
        }
