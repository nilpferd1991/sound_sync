import alsaaudio
from sound_sync.informationBase import ReadFromConfig

__author__ = 'nilpferd'


class PCMPlay(ReadFromConfig):
    # The PCM device of the ALSA-Loopback-Adapter. The data coming from the applications
    # is send through this loopback into the program. We need a frame rate of 44100 Hz and collect 10 ms of data
    # at once.

    def __init__(self):
        self.pcm = None
        ReadFromConfig.__init__(self)

    def initialize_pcm(self, frame_rate, buffer_size):
        """
        Set the PCM device with the usual parameters.
        """
        self.pcm = alsaaudio.PCM(card="default", type=alsaaudio.PCM_PLAYBACK, mode=alsaaudio.PCM_NONBLOCK)
        self.pcm.setchannels(int(self.get_attribute("channels")))
        self.pcm.setrate(frame_rate)
        self.pcm.setformat(alsaaudio.PCM_FORMAT_S16_LE)
        self.pcm.setperiodsize(int(buffer_size/float(self.get_attribute("sound_data_size"))))

    def play_buffer(self, data):
        return self.pcm.write(bytes(data))


