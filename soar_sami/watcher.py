#!/usr/bin/env python 
# -*- coding: utf8 -*-

import os
import time

from watchdog.observers import Observer
from watchdog.events import LoggingEventHandler
from watchdog.events import FileSystemEventHandler

from soar_sami.io.sami_log import SAMILog

__author__ = 'Bruno Quint'


def watch(path):

    # event_handler = SAMIFileHandler()
    # data_watcher = DataWatcher(event_handler, path=path)
    # data_watcher.schedule(event_handler, path)
    # data_watcher.start()
    #
    # try:
    #     while True:
    #         time.sleep(1)
    # except KeyboardInterrupt:
    #     data_watcher.unschedule(event_handler)
    #     data_watcher.stop()
    #
    # data_watcher.join()
    # logger.info('Finished process')

    event_handler = LoggingEventHandler()
    observer = Observer()
    observer.schedule(event_handler, path, recursive=True)
    observer.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()

    observer.join()


class DataWatcher(Observer):

    def __init__(self, event_handler, debug=False, path=None):

        super(DataWatcher, self).__init__()

        if debug:
            logger.set_debug()

        if path is None:
            path = os.getcwd()

        self.path = path
        self.event_handler = event_handler

    def run(self):

        number_of_files = len([name
                               for name
                               in os.listdir(self.path)
                               if os.path.isfile(os.path.join(self.path, name))])

        logger.info('SAMI watchdog started on folder: {:s}'.format(self.path))
        logger.info('Folder contains: {:d} files'.format(number_of_files))

    def schedule(self):
        super(DataWatcher, self).schedule(self.event_handler, self.path)

    def unschedule(self):
        super(DataWatcher, self).unschedule(self.event_handler)


class SAMIFileHandler(FileSystemEventHandler):

    def catch_all_handler(self, event):
        pass

    def on_moved(self, event):
        print("MOVED " + str(event))
        self.catch_all_handler(event)

    def on_created(self, event):
        print("CREATED " + str(event))
        self.catch_all_handler(event)

    def on_deleted(self, event):
        print("DELETED " + str(event))
        self.catch_all_handler(event)

    def on_modified(self, event):
        print("MODIFIED " + str(event))
        self.catch_all_handler(event)