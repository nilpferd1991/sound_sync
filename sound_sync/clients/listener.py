import json
import urllib
from tornado import httpclient


class Listener:
    def __init__(self):
        from sound_sync.audio.pcm.play import PCMPlay

        self.http_client = httpclient.AsyncHTTPClient()
        self.host = None
        self.manager_port = None
        self.handler_port = None
        self.channel_hash = None
        self.client_hash = None
        self.player = PCMPlay()

        self.name = None
        self.description = None

    def initialize(self):
        if self.client_hash is not None:
            return

        if self.channel_hash is None:
            raise ValueError("You have to set the hash of the channel you want to listen to.")

        http_client = httpclient.HTTPClient()

        self.add_client_to_server(http_client)
        self.get_settings(http_client)
        self.set_name_and_address_of_client(http_client)
        self.player.initialize()

    @property
    def manager_string(self):
        return "http://" + str(self.host) + ":" + str(self.manager_port)

    @property
    def handler_string(self):
        if self.handler_port is None:
            raise ValueError()

        return "http://" + str(self.host) + ":" + str(self.handler_port)

    def add_client_to_server(self, http_client):
        response = http_client.fetch(self.manager_string + "/clients/add")
        self.client_hash = response.body

    def main_loop(self):
        if self.client_hash is None:
            raise AssertionError("Listener needs to be initialized first")

        http_client = httpclient.HTTPClient()

        # TODO

        #while True:
        #    sound_buffer, length = self.recorder.get()
        #    parameters = {"buffer": sound_buffer}
        #    body = urllib.urlencode(parameters)
        #    http_client.fetch(self.manager_string + '/channels/' + self.channel_hash + '/buffers/add',
        #                      method="POST", body=body)

    def terminate(self):
        if self.client_hash is None:
            return

        http_client = httpclient.HTTPClient()

        self.remove_client_from_server(http_client)

    def remove_client_from_server(self, http_client):
        http_client.fetch(self.manager_string + "/clients/delete/" + self.client_hash)
        self.client_hash = None

    def get_settings(self, http_client):
        response = http_client.fetch(self.manager_string + "/channels/get")
        response_dict = json.loads(response.body)

        if self.channel_hash not in response_dict:
            raise KeyError("The channel_hash you selected is not registered on the server.")

        channel_information = response_dict[self.channel_hash]
        self.player.buffer_size = channel_information["buffer_size"]
        self.player.frame_rate = channel_information["frame_rate"]
        self.player.channels = channel_information["channels"]
        self.player.factor = channel_information["factor"]
        self.handler_port = channel_information["handler_port"]

    def list_channels(self):
        http_client = httpclient.HTTPClient()
        response = http_client.fetch(self.manager_string + "/channels/get")
        response_dict = json.loads(response.body)

        for channel_hash, channel in response_dict.iteritems():
            print channel

    def set_name_and_address_of_client(self, http_client):
        # TODO
        ip_address = "None"
        parameters = {"name": self.name,
                      "ip_address": ip_address}
        body = urllib.urlencode(parameters)
        http_client.fetch(self.manager_string + "/clients/set/" + self.client_hash, body=body, method="POST")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser()
    parser.add_argument("-i", "--hostname",
                        default="192.168.178.100",
                        type=str,
                        help="Hostname of the management server.",
                        dest="hostname")

    parser.add_argument("-p", "--port",
                        default=8888,
                        type=int,
                        help="Port of the management socket on the management server. Default 8888.",
                        dest="manager_port")

    parser.add_argument("-c", "--channel_hash",
                        default=None,
                        type=str,
                        help="Hash of the channel to listen to. If not given, list all channels. ",
                        dest="channel_hash")

    parser.add_argument("-n", "--name",
                        default="Untitled",
                        type=str,
                        help="Name of this client in the client list. Default Untitled.",
                        dest="name")

    args = parser.parse_args()

    listener = Listener()
    listener.host = args.hostname
    listener.manager_port = args.manager_port
    listener.name = args.name

    if args.channel_hash is not None:
        listener.channel_hash = args.channel_hash
        listener.initialize()

        try:
            listener.main_loop()
        finally:
            listener.terminate()

    else:
        listener.list_channels()