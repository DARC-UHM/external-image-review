import datetime
import logging
import threading

from mongoengine import DoesNotExist
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

from schema.annotator import Annotator
from schema.reviewer import Reviewer, SlackMessage


class SlackHelper:
    def __init__(self,
                 reviewer: str,
                 sequence: str,
                 annotator: str,
                 slack_client: WebClient,
                 slack_channel_id: str,
                 logger: logging.Logger):
        self.reviewer = reviewer
        self.sequence = sequence
        self.annotator = annotator
        self.emoji = ':ocean:'
        self.slack_client = slack_client
        self.slack_channel_id = slack_channel_id
        self.logger = logger

    def send_message(self):
        slack_thread = threading.Thread(target=self._send_message, args=())
        slack_thread.start()

    def _send_message(self):
        annotators = {self.annotator}
        sequences = {self._get_short_sequence_name(self.sequence)}
        count = 1
        try:
            db_record = Reviewer.objects.get(name=self.reviewer)
            self.emoji = self._get_reviewer_emoji(db_record.phylum.split(',')[0])
        except DoesNotExist:
            self.logger.error(f'No reviewer record found for {self.reviewer}')
            return
        if db_record.slack_message:
            scheduled_time = db_record.slack_message.scheduled_time
            if scheduled_time and scheduled_time > datetime.datetime.now() + datetime.timedelta(minutes=5):
                self._delete_scheduled_message(db_record.slack_message.scheduled_message_id)
                for annotator in db_record.slack_message.annotators:
                    annotators.add(annotator)
                for sequence in db_record.slack_message.dives:
                    sequences.add(sequence)
                count += db_record.slack_message.count

        new_scheduled_time = datetime.datetime.now() + datetime.timedelta(minutes=35)
        scheduled_message_id = self._schedule_new_message(
            scheduled_time=new_scheduled_time.strftime('%s'),
            annotators=list(annotators),
            sequences=list(sequences),
            count=count,
        )
        if scheduled_message_id:
            db_record.slack_message = SlackMessage(
                count=count,
                annotators=list(annotators),
                dives=list(sequences),
                scheduled_message_id=scheduled_message_id,
                scheduled_time=new_scheduled_time,
            )
            db_record.save()

    def _delete_scheduled_message(self, scheduled_message_id):
        try:
            self.slack_client.chat_deleteScheduledMessage(
                channel=self.slack_channel_id,
                scheduled_message_id=scheduled_message_id,
            )
            self.logger.info(f'Deleted existing scheduled message for {self.reviewer} ({scheduled_message_id})')
        except SlackApiError as e:
            self.logger.error(f'Error deleting scheduled message for {self.reviewer} with id {scheduled_message_id}: {e}')

    def _schedule_new_message(self, scheduled_time: str, annotators: list[str], sequences: list[str], count: int) -> str | None:
        try:
            result = self.slack_client.chat_scheduleMessage(
                channel=self.slack_channel_id,
                post_at=scheduled_time,
                text=f"New comments from {self.reviewer} {self.emoji}",
                blocks=self._get_blocks(annotators, sequences, count),
            )
            self.logger.info(f'Scheduled new message for {self.reviewer} ({result.get('scheduled_message_id')})')
            return result.get('scheduled_message_id')
        except SlackApiError as e:
            self.logger.error(f'Error: {e}')

    def _get_blocks(self, annotators: list[str], sequences: list[str], count: int) -> list:
        annotator_ids = [self._get_annotator_slack_id(annotator) for annotator in annotators]
        return [
            {
                "type": "markdown",
                "text": f"> **New comments from {self.reviewer} {self.emoji}**\n> \n"
                        f"> {self.reviewer} added {count} new comment{'' if count == 1 else 's'} from "
                        f"**{self._formatted_comma_list(sequences)}** "
                        f"(annotator{'' if len(annotators) == 1 else 's'} {self._formatted_comma_list(annotator_ids)})."
            }
        ]

    def _get_annotator_slack_id(self, annotator_name: str) -> str:
        try:
            return Annotator.objects.get(name=annotator_name).slack_id or annotator_name
        except DoesNotExist:
            self.logger.error(f'No annotator record found for {annotator_name}')
            return annotator_name

    @staticmethod
    def _get_short_sequence_name(sequence: str) -> str:
        if 'Hercules' in sequence:
            return f'Hercules {sequence.split("Hercules ")[1][:3]}'
        if 'Deep Discoverer' in sequence:
            return f'Deep Discoverer {sequence.split("Deep Discoverer ")[1][:4]}'
        return sequence

    @staticmethod
    def _formatted_comma_list(items: list) -> str:
        sorted_list = sorted(items)
        if len(sorted_list) == 1:
            return sorted_list[0]
        if len(sorted_list) == 2:
            return f'{sorted_list[0]} and {sorted_list[1]}'
        return f'{", ".join(list(sorted_list)[:-1])}, and {list(sorted_list)[-1]}'

    @staticmethod
    def _get_reviewer_emoji(phylum) -> str:
        match phylum:
            case 'Cnidaria':
                return ':coral:'
            case 'Mollusca':
                return ':octopus:'
            case 'Arthropoda':
                return ':crab:'
            case 'Echinodermata':
                return ':starfish:'
            case 'Chordata':
                return ':fish:'
            case 'Annelida':
                return ':worm:'
            case 'Bryozoa':
                return ':coral:'
            case 'Porifera':
                return ':sponge:'
            case 'Ctenophora':
                return '🪼'
            case 'Retaria':
                return ':microbe:'
            case _:
                return ':ocean:'
