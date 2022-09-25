import datetime
import os
from flask import (
    Flask,
    session,
    render_template,
    request,
    redirect,
    url_for,
)
from google.auth.transport import requests
from google.cloud import datastore
import google.oauth2.id_token


app = Flask(__name__)
app.secret_key = os.urandom(24)
datastore_client = datastore.Client()
firebase_request_adapter = requests.Request()


def user_authenticated():
    """
    Checks if user is authenticated
    If so, returns dict with claims
    Otherwise session is set to None
    """
    id_token = request.cookies.get("token")
    out = {"user_info": None, "err": None}

    if id_token:
        try:
            # Verify the token against the Firebase Auth API
            claims = google.oauth2.id_token.verify_firebase_token(
                id_token, firebase_request_adapter
            )
            # set user session to user id
            session["usr"] = claims["user_id"]

            # store time of authentication check
            store_time(
                claims["email"],
                datetime.datetime.now(tz=datetime.timezone.utc),
            )

            out["user_info"] = claims
            return out

        except ValueError as exc:
            out["err"] = str(exc)
            return out

    session["usr"] = None
    return out


def store_time(email, dt):
    """Storing last login to Datastore"""
    entity = datastore.Entity(key=datastore_client.key("User", email, "visit"))
    entity.update({"timestamp": dt})
    datastore_client.put(entity)


def fetch_times(email, limit=1):
    """Fetching most recent login time from Datastore"""
    ancestor = datastore_client.key("User", email)
    query = datastore_client.query(kind="visit", ancestor=ancestor)
    query.order = ["-timestamp"]
    times = query.fetch(limit)

    return times


def fetch_glist_items(email):
    """
    Fetching grocery list times from Datastore
    Items are returned sorted by done, priority, name
    """
    ancestor = datastore_client.key("User", email)
    query = datastore_client.query(kind="list_item", ancestor=ancestor)
    query.order = ["done", "-important", "item_name"]
    # query.order = ["-item_name","-important","-done"]

    items = query.fetch()
    return items


def switch_status(property, item_id, email):
    """Updating importance / done status"""

    # get entity
    entity = datastore_client.get(
        datastore_client.key("User", email, "list_item", int(item_id))
    )

    # checking status and switching
    if entity[property] == 1:
        new_val = 0
    else:
        new_val = 1

    entity.update({property: new_val})
    datastore_client.put(entity)


@app.route("/")
def root():
    """Render root; user redirected to login if not authenticated"""
    error_message = None
    times = None
    items = None

    # Verify Firebase auth.
    check_auth = user_authenticated()

    if session["usr"]:
        times = fetch_times(check_auth["user_info"]["email"])
        items = fetch_glist_items(check_auth["user_info"]["email"])

        return render_template(
            "index.html",
            user_data=check_auth["user_info"],
            error_message=error_message,
            times=times,
            items=items,
        )

    return redirect(url_for("login"))


@app.route("/login")
def login():
    """Render root if user authenticated, root otherwise"""
    user_authenticated()
    if session["usr"]:
        return redirect(url_for("root"))
    return render_template("login.html")


@app.route("/add_grocery_item", methods=["GET", "POST"])
def add_glist_item():
    """Add entity from database if user authenticated"""

    # Verify Firebase auth.
    check_auth = user_authenticated()

    if request.method == "POST":
        item_name = request.form.get("content")
        if item_name == "":
            item_name = "I'm feeling lucky"

        item = {
            "item_name": item_name,
            "important": 0,
            "done": 0,
        }

        entity = datastore.Entity(
            key=datastore_client.key(
                "User", check_auth["user_info"]["email"], "list_item"
            )
        )
        entity.update(
            {
                "item_name": item["item_name"],
                "important": item["important"],
                "done": item["done"],
            }
        )
        datastore_client.put(entity)

    return redirect(url_for("root"))


@app.route("/change_important_status/<string:item_id>")
def update_important_status(item_id):
    """Route for update Important status"""
    check_auth = user_authenticated()
    if session["usr"]:
        switch_status("important", item_id, check_auth["user_info"]["email"])
    return redirect(url_for("root"))


@app.route("/change_done_status/<string:item_id>")
def update_done_status(item_id):
    """Route for update Done status"""
    check_auth = user_authenticated()
    if session["usr"]:
        switch_status("done", item_id, check_auth["user_info"]["email"])
    return redirect(url_for("root"))


@app.route("/signout")
def signout():
    """Route for update Done status"""
    session["usr"] = None
    return redirect(url_for("login"))


@app.route("/delete_item/<string:item_id>")
def delete_glist_item(item_id):
    """Delete entity from database if user authenticated"""
    check_auth = user_authenticated()
    if session["usr"]:
        key = datastore_client.key(
            "User", check_auth["user_info"]["email"], "list_item", int(item_id)
        )
        datastore_client.delete(key)
    return redirect(url_for("root"))


@app.route("/clear_glist", methods=["POST"])
def clear_glist():
    """Function to fully clear list"""
    check_auth = user_authenticated()
    if session["usr"]:
        items = fetch_glist_items(check_auth["user_info"]["email"])
        for item in items:
            delete_glist_item(item.key.id)
    return redirect(url_for("root"))


if __name__ == "__main__":
    # This is used when running locally only.
    # Flask's development server will automatically serve static files in
    # the "static" directory. See:
    # http://flask.pocoo.org/docs/1.0/quickstart/#static-files. Once deployed,
    # App Engine itself will serve those files as configured in app.yaml.
    app.run(host="127.0.0.1", port=8080, debug=True)
