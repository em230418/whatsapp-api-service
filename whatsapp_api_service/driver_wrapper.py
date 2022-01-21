# this file is based on https://github.com/mukulhase/WebWhatsapp-Wrapper/blob/master/sample/flask/webapi.py
# Copyright 2018 Nishant Bhatia <nishant@roshi.in>
# License MIT (https://opensource.org/licenses/MIT).

import shutil
import os
from flask.json import JSONEncoder

from webwhatsapi import MessageGroup, WhatsAPIDriver, WhatsAPIDriverStatus
from webwhatsapi.objects.whatsapp_object import WhatsappObject

# Seleneium Webdriver configuration
CHROME_CACHE_PATH = os.environ.get("FIREFOX_PROFILE_DIR", "/tmp/chrome_cache")

# Driver store all the instances of webdriver for each of the client user
drivers = dict()


class WhatsAPIJSONEncoder(JSONEncoder):
    def default(self, obj):
        if isinstance(obj, WhatsappObject):
            return obj.get_js_obj()
        if isinstance(obj, MessageGroup):
            return obj.chat
        return super(WhatsAPIJSONEncoder, self).default(obj)


def get_profile_dir(client_id):
    return CHROME_CACHE_PATH + "/" + str(client_id)


def init_client(client_id):
    """Initialse a driver for client and store for future reference

    @param client_id: ID of client user
    @return whebwhatsapi object
    """
    if client_id not in drivers:
        drivers[client_id] = init_driver(client_id)
    return drivers[client_id]


def init_driver(client_id):
    """Initialises a new driver via webwhatsapi module

    @param client_id: ID of user client
    @return webwhatsapi object
    """

    # Create profile directory if it does not exist
    profile_path = get_profile_dir(client_id)
    if not os.path.exists(profile_path):
        os.makedirs(profile_path)

    # Create a whatsapidriver object
    print("profile_path", profile_path)
    return WhatsAPIDriver(
        profile=profile_path,
        extra_params={"service_log_path": "/tmp/geckodriver.log"},
    )


def delete_client(client_id, preserve_cache=False):
    """Delete all objects related to client

    @param client_id: ID of client user
    @param preserve_cache: Boolean, whether to delete the chrome profile folder or not
    """
    drivers.pop(client_id).quit()

    if not preserve_cache:
        pth = get_profile_dir(client_id)
        shutil.rmtree(pth)


def prepare_app(app):
    app.json_encoder = WhatsAPIJSONEncoder
