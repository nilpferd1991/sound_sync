import urllib

from sound_sync.clients.connection import SoundSyncConnection
from sound_sync.rest_server.server_items.json_pickable import JSONPickleable
from sound_sync.rest_server.server_items.server_items import Client, Channel
from sound_sync.timing.time_utils import get_current_date, waiting_time_to_datetime


class BaseListener(Client):
    def __init__(self, channel_hash=None, host=None, manager_port=None):
        Client.__init__(self)

        #: The connection to the rest server
        self.connection = SoundSyncConnection(host, manager_port)

        #: The channel hash of the channel we want to listen to
        self.channel_hash = channel_hash

        #: The channel we are listening to
        self._connected_channel = None

        #: The player to send the data to
        self.player = None

    def initialize(self):
        if self.client_hash is not None:
            return

        self.client_hash = self.connection.add_client_to_server()
        self.get_settings()
        self.connection.set_name_of_client(self.name, self.client_hash)

        self.player.initialize()

    @property
    def handler_string(self):
        if self._connected_channel is None or self._connected_channel.handler_port is None:
            raise ValueError()

        return "http://" + str(self.connection.host) + ":" + str(self._connected_channel.handler_port)

    def terminate(self):
        if self.client_hash is None:
            return

        self.connection.remove_client_from_server(self.client_hash)
        self.client_hash = None

        self.player.terminate()

    def get_settings(self):
        channel_information = self.connection.get_channel_information(self.channel_hash)

        JSONPickleable.fill_with_json(self.player, channel_information)
        self._connected_channel = Channel()
        JSONPickleable.fill_with_json(self._connected_channel, channel_information)

    def main_loop(self):
        if self.client_hash is None:
            raise AssertionError("Listener needs to be initialized first")

        # Receive as many packages as possible (to have a good starting point)

        # Start the thread to put sound buffers in the audio queue

        # Receive information from the buffer server if possible

    def calculate_next_starting_time_and_buffer(self):
        current_time = get_current_date()
        start_time = self.player.start_time

        waiting_time = self.player.get_waiting_time()

        if current_time < start_time:
            raise ValueError("Can not use start times in the future")

        time_delta = current_time - start_time
        print time_delta.total_seconds() / waiting_time
        number_of_passed_clocks = int(time_delta.total_seconds() / waiting_time)
        number_of_next_clock = number_of_passed_clocks + 1
        next_time = start_time + waiting_time_to_datetime(number_of_next_clock * waiting_time)

        return next_time, number_of_next_clock


class BaseSender(Channel):
    def __init__(self, host=None, manager_port=None):
        Channel.__init__(self)

        #: The connection to the rest server
        self.connection = SoundSyncConnection(host, manager_port)

        #: The recorder used for recording the sound data
        self.recorder = None

    def initialize(self):
        if self.channel_hash is not None:
            return

        self.channel_hash = self.connection.add_channel_to_server()
        self.get_settings()
        self.connection.set_name_and_description_of_channel(self.name, self.description, self.channel_hash)

        self.recorder.initialize()

    def main_loop(self):
        if self.channel_hash is None:
            raise AssertionError("Sender needs to be initialized first")

        while True:
            sound_buffer, length = self.recorder.get()
            parameters = {"buffer": sound_buffer}
            body = urllib.urlencode(parameters)
            self.connection.http_client.fetch(self.handler_string + '/add',
                                   method="POST", body=body)

    def terminate(self):
        if self.channel_hash is None:
            return

        self.connection.remove_channel_from_server(self.channel_hash)
        self.channel_hash = None

    def get_settings(self):
        channel_information = self.connection.get_channel_information(self.channel_hash)

        JSONPickleable.fill_with_json(self.recorder, channel_information)
        self.handler_port = channel_information["handler_port"]

    @property
    def handler_string(self):
        if self.handler_port is None:
            raise ValueError()

        return "http://" + str(self.connection.host) + ":" + str(self.handler_port)