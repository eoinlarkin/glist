import datetime
from flask import Flask, render_template, request, redirect, url_for
from google.auth.transport import requests
from google.cloud import datastore
import google.oauth2.id_token

datastore_client = datastore.Client()


app = Flask(__name__)


def user_authenticated():
    id_token = request.cookies.get("token")
    out = {"auth": False, "user_info": None, "err": None}

    if id_token:
        try:
            # Verify the token against the Firebase Auth API. This example
            # verifies the token on each page load. For improved performance,
            # some applications may wish to cache results in an encrypted
            # session store (see for instance
            # http://flask.pocoo.org/docs/1.0/quickstart/#sessions).
            claims = google.oauth2.id_token.verify_firebase_token(
                id_token, firebase_request_adapter
            )
            out["auth"], out["user_info"] = True, claims
            return out
        except ValueError as exc:
            out['err'] = str(exc)
        

    #out["auth"], out["err"] = False, "insert error code"
    return out


def store_time(email, dt):
    entity = datastore.Entity(key=datastore_client.key("User", email, "visit"))
    entity.update({"timestamp": dt})

    datastore_client.put(entity)


# def store_glist_item(email, dt):


def fetch_times(email, limit):
    ancestor = datastore_client.key("User", email)
    query = datastore_client.query(kind="visit", ancestor=ancestor)
    query.order = ["-timestamp"]

    times = query.fetch(limit=limit)

    return times


def fetch_glist_items(email, limit):
    ancestor = datastore_client.key("User", email)
    query = datastore_client.query(kind="list_item", ancestor=ancestor)
    # query.order = ["-item_name"]

    items = query.fetch(limit=limit)

    # vars(items)
    # for x in items:
    #     print(x.key.id)

    # for x in items:
    #     print(x['item_name'])

    # print('printing item name status')
    # for x in items:
    #     print(x['item_name'])

    return items


firebase_request_adapter = requests.Request()


@app.route("/")
def root():
    error_message = None
    times = None
    items = None

    # Verify Firebase auth.
    check_auth = user_authenticated()

    if check_auth["auth"] is True:
        store_time(
            check_auth["user_info"]["email"],
            datetime.datetime.now(tz=datetime.timezone.utc),
        )
        times = fetch_times(check_auth["user_info"]["email"], 1)
        items = fetch_glist_items(check_auth["user_info"]["email"], 10)

    return render_template(
        "index.html",
        user_data=check_auth["user_info"],
        error_message=error_message,
        times=times,
        items=items,
    )


@app.route("/add_grocery_item", methods=["GET", "POST"])
def add_glist_item():
    id_token = request.cookies.get("token")
    error_message = None
    if request.method == "POST":

        if id_token:
            try:
                # Verify the token against the Firebase Auth API. This example
                # verifies the token on each page load. For improved
                # performance, some applications
                # may wish to cache results in an encrypted
                # session store (see for instance
                # http://flask.pocoo.org/docs/1.0/quickstart/#sessions).
                claims = google.oauth2.id_token.verify_firebase_token(
                    id_token, firebase_request_adapter
                )

            except ValueError as exc:
                # This will be raised if the token is expired or any other
                # verification checks fail.
                error_message = str(exc)

        print(error_message)

        item = {
            "item_name": request.form.get("content"),
            "important": 0,
            "done": 0,
        }
        # print(item["item_name"])

        entity = datastore.Entity(
            key=datastore_client.key("User", claims["email"], "list_item")
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


@app.route("/delete_item/<string:item_id>")
def delete_glist_item(item_id):

    id_token = request.cookies.get("token")
    error_message = None

    if id_token:
        try:
            # Verify the token against the Firebase Auth API. This example
            # verifies the token on each page load. For improved
            # performance, some applications
            # may wish to cache results in an encrypted
            # session store (see for instance
            # http://flask.pocoo.org/docs/1.0/quickstart/#sessions).
            claims = google.oauth2.id_token.verify_firebase_token(
                id_token, firebase_request_adapter
            )

        except ValueError as exc:
            # This will be raised if the token is expired or any other
            # verification checks fail.
            error_message = str(exc)

        print(error_message)
        print(item_id)

        key = datastore_client.key(
            "User", claims["email"], "list_item", int(item_id)
        )
        print(f"This is the key {key}")
        datastore_client.delete(key)

    return redirect(url_for("root"))


if __name__ == "__main__":
    # This is used when running locally only.
    # Flask's development server will automatically serve static files in
    # the "static" directory. See:
    # http://flask.pocoo.org/docs/1.0/quickstart/#static-files. Once deployed,
    # App Engine itself will serve those files as configured in app.yaml.
    app.run(host="127.0.0.1", port=8080, debug=True)
