import traceback
import json
from flask import Flask, render_template, g, abort, request, jsonify
from werkzeug.exceptions import HTTPException
from collections import defaultdict
from functools import wraps
import threading
import requests
import logging
from uuid import uuid4

from .driver_wrapper import (
    WhatsAPIDriverStatus,
    WhatsAPIJSONEncoder,
    delete_client,
    get_profile_dir,
    init_client,
    prepare_app,
)

from . import db


class MessageObserver:
    def __init__(self, client_id, webhook_url=None):
        self.client_id = client_id
        self.webhook_url = webhook_url

    def set_webhook_url(self, webhook_url):
        db.set_webhook_url(self.client_id, webhook_url)
        self.webhook_url = webhook_url

    def unset_webhook_url(self):
        self.set_webhook_url(None)

    def send_message_to_webhook(self, message):
        webhook_url = self.webhook_url
        app.logger.debug(json.dumps(message, cls=WhatsAPIJSONEncoder, sort_keys=True, indent=2))
        data = message.get_js_obj()
        data["fromMe"] = False
        data["senderName"] = data["sender"]["pushname"]
        data["chatName"] = data["chat"]["contact"]["pushname"]
        data["author"] = data["sender"]["id"]["_serialized"]
        data["chatId"] = data["chatId"]["_serialized"]
        app.logger.debug(json.dumps(data, sort_keys=True, indent=2))
        try:
            app.logger.debug("sending webhook to %s" % (webhook_url,))
            requests.post(webhook_url, json={"messages": [data]}, timeout=10)
            app.logger.debug("done sending webhook to %s" % (webhook_url,))
        except requests.exceptions.RequestException:
            app.logger.exception("error while sending webhook")

    def on_message_received(self, new_messages):
        app.logger.info("New messages received")

        for message in new_messages:
            if message.type == "chat":
                self.send_message_to_webhook(message)
            else:
                app.logger.warning("Received message with type %s" % (message.type,))


app = Flask(__name__, template_folder="templates")
semaphores = defaultdict(lambda: threading.Semaphore())
drivers = {}
message_observers = {}
logger = logging.getLogger(__name__)


def uses_driver(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        with app.app_context():
            token = request.args["token"]
            user = db.get_user_by_token(token)
            if not user:
                abort(401, "Must be logged in")

            g.user = user
            with semaphores[user["id"]]:
                g.driver = init_client(user["name"])

            return f(*args, **kwargs)

    return wrap


@app.errorhandler(Exception)
def handle_exception(e):
    if isinstance(e, HTTPException):
        return e
    traceback.print_exc()
    return jsonify(
        name = type(e).__module__ + "." + type(e).__name__ if type(e).__module__ else type(e).__name__,
        debug = traceback.format_exc(),
        message = str(e),
        arguments = e.args,
    ), 500


@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()


@app.route("/admin", methods=["GET", "POST"])
def admin_endpoint():
    if request.remote_addr != "127.0.0.1":
        abort(403, "Only loopback requests are allowed")

    users = []

    if request.method == "POST":
        if request.form["action"] == "generate_access_token":
            token = str(uuid4())
            db.create_user(request.form["profile_name"], token)

        else:
            raise NotImplementedError("Unknown action: %s" % (request.form["action"],))

    users = db.get_all_users()
    return render_template(
        "admin.html",
        users=users,
    )


# TODO: api methods should return only json. even on error
# maybe we can have @api decorator that also checks access tokens?
@app.route("/webhook", methods=["POST"])
@uses_driver
def set_webhook():
    user_id = g.user["id"]
    webhook_url = request.get_json()["webhookUrl"]
    if user_id not in message_observers:
        message_observers[user_id] = MessageObserver(user_id)
        g.driver.subscribe_new_messages(message_observers[user_id])
    message_observers[user_id].set_webhook_url(webhook_url)
    return jsonify(ok=True)


@app.route("/sendMessage", methods=["POST"])
@uses_driver
def send_message():
    request_json = request.get_json()
    chat_id = request_json["chatId"]
    body = request_json["body"]
    return jsonify(g.driver.chat_send_message(chat_id, body))


@app.route("/sendFile", methods=["POST"])
@uses_driver
def send_file():
    raise NotImplementedError("n/a")
    request_json = request.get_json()
    chat_id = request_json["chatId"]
    body = request_json["body"]
    filename = request_json["filename"]
    caption = request_json["caption"]
    # TODO: send file
    return jsonify(g.driver.chat_send_message(chat_id, body))


@app.route("/driver/ping", methods=["GET"])
@uses_driver
def ping():
    return jsonify(ok=True)


prepare_app(app)
for row in db.get_all_webhooks():
    driver = init_client(row["user_name"])
    user_id = row["user_id"]
    if user_id not in message_observers:
        message_observers[user_id] = MessageObserver(user_id)
    message_observers[user_id].webhook_url = row["webhook_url"]
    driver.subscribe_new_messages(message_observers[user_id])
    logger.setLevel(logging.DEBUG)
    app.logger.debug(repr(message_observers))
