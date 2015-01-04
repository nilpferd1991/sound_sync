import time
from multiprocessing import Lock

mutex = Lock()

__author__ = 'nilpferd'


class IndexToLowException(Exception):
    def __init__(self):
        pass


class IndexToHighException(Exception):
    def __init__(self):
        pass


class EmptyException(Exception):
    def __init__(self):
        pass


class BufferListHandler:
    def __init__(self):
        self.buffers = list()
        self.start_time = 0
        self.start_buffer_index = 0
        self.end_buffer_index = -1

    def add_buffer(self, sound_buffer):
        mutex.acquire()
        self.buffers.append(sound_buffer)
        self.end_buffer_index += 1

        if len(self.buffers) > 50:
            self.buffers.pop(0)
            self.start_buffer_index += 1

        mutex.release()

    def is_empty(self):
        return len(self.buffers) == 0

    def get_buffer_by_buffer_index(self, index):
        return self.buffers[index - self.start_buffer_index]


class ClientListHandler(BufferListHandler):
    def __init__(self):
        self.listener_list = dict()
        self.sender = None
        BufferListHandler.__init__(self)

    def add_listener(self, listener_socket):
        if not self.is_listener(listener_socket):
            self.listener_list[listener_socket] = self.start_buffer_index

    def is_listener(self, listener_socket):
        return listener_socket in self.listener_list

    def get_buffer(self, listener_socket):
        mutex.acquire()
        search_index = self.listener_list[listener_socket]
        if search_index < self.start_buffer_index:
            self.listener_list[listener_socket] = self.start_buffer_index
        elif search_index > self.end_buffer_index:
            mutex.release()
            return None, None

        search_index = self.listener_list[listener_socket]
        return_buffer = self.buffers[search_index - self.start_buffer_index]
        self.listener_list[listener_socket] += 1
        mutex.release()
        return search_index, return_buffer

    def remove_listener(self, listener_socket):
        if self.is_listener(listener_socket):
            del self.listener_list[listener_socket]

    def add_sender(self, sender_socket):
        if not self.is_sender(sender_socket):
            self.sender = sender_socket
            BufferListHandler.__init__(self)
            self.start_time = time.time()

    def is_sender(self, sender_socket):
        return self.sender == sender_socket

    def no_sender(self):
        return self.sender is None

    def remove_sender(self):
        self.sender = None


class ClientBufferListHandler(BufferListHandler):
    def __init__(self):
        self.current_buffer_index = -1
        BufferListHandler.__init__(self)

    def add_buffer_with_index(self, sound_buffer, buffer_index):
        if buffer_index == self.end_buffer_index + 1:
            self.add_buffer(sound_buffer)
        else:
            raise IndexError

    def get_current_playable_buffer(self):
        if self.current_buffer_index > self.end_buffer_index:
            raise IndexError
        self.current_buffer_index += 1
        return self.get_buffer_by_buffer_index(self.current_buffer_index - 1)