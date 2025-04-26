import logging
import os
from http.client import HTTPException
from io import BytesIO

import requests
from PIL import Image


class TatorFrameFetcher:
    """
    Fetches a frame from Tator, crops the frame, and saves it to the file system.
    """

    def __init__(
        self,
        localization_id: str,
        localization_media_id: int,
        localization_frame: int,
        localization_type: int,
        normalized_top_left_x_y: tuple,
        normalized_dimensions: tuple,
        tator_url: str,
        logger: logging.Logger,
    ):
        self.localization_data = {
            'id': localization_id,
            'media_id': localization_media_id,
            'frame': localization_frame,
            'type': localization_type,
            'normalized_top_left_x_y': normalized_top_left_x_y,
            'normalized_dimensions': normalized_dimensions,
        }
        self.tator_url = tator_url
        self.logger = logger
        self.pil_image = None
        self.image_name = f'{localization_id}.jpg'
        self.thumbnail_name = f'{localization_id}_thumbnail.jpg'

    def fetch_frame(self):
        frame_res = requests.get(
            url=f'{self.tator_url}/rest/GetFrame/{self.localization_data["media_id"]}?frames={self.localization_data["frame"]}',
            headers={
                'Authorization': f'Token {os.environ.get("TATOR_TOKEN")}',
                'accept': 'image/*',
            },
        )
        if frame_res.status_code != 200:
            self.logger.error(f'Error retrieving frame from Tator: {frame_res.text}')
            raise HTTPException('Error retrieving frame info from Tator', 400)
        self.pil_image = Image.open(BytesIO(frame_res.content))

    def save_images(self, save_path: str):
        image_path = os.path.join(save_path, self.image_name)
        thumbnail_path = os.path.join(save_path, self.thumbnail_name)
        if self.localization_data['type'] == 48:  # 48 is BOX, crop the image
            normalized_top_left_x = self.localization_data['normalized_top_left_x_y'][0]
            normalized_top_left_y = self.localization_data['normalized_top_left_x_y'][1]
            normalized_width = self.localization_data['normalized_dimensions'][0]
            normalized_height = self.localization_data['normalized_dimensions'][1]
            # convert to pixel coordinates
            width = self.pil_image.width
            height = self.pil_image.height
            left = int(normalized_top_left_x * width)
            upper = int(normalized_top_left_y * height)
            right = int((normalized_top_left_x + normalized_width) * width)
            lower = int((normalized_top_left_y + normalized_height) * height)
            aspect_ratio = (right - left) / (lower - upper)
            # if aspect ratio is not 16:9, expand the crop box to fit
            if aspect_ratio < 16 / 9:  # expand the width
                current_width = right - left
                new_width = (lower - upper) * 16 / 9
                left -= (new_width - current_width) // 2
                right += (new_width - current_width) // 2
            elif aspect_ratio > 16 / 9:  # expand the height
                current_height = lower - upper
                new_height = (right - left) * 9 / 16
                upper -= (new_height - current_height) // 2
                lower += (new_height - current_height) // 2
            # check if the crop box is within the image bounds
            if left < 0:
                right += abs(left)
                left = 0
            if upper < 0:
                lower += abs(upper)
                upper = 0
            if right > width:
                left -= right - width
                right = width
            if lower > height:
                upper -= lower - height
                lower = height
            self.pil_image = self.pil_image.crop((left, upper, right, lower))
        self.pil_image.save(image_path)
        self.pil_image.thumbnail((600, 600))
        self.pil_image.save(thumbnail_path)
