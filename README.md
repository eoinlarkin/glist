# glist

A very simple grocery list tracker


- [Overview](#overview)
- [Features](#features)
- [Technologies](#technologies)
- [Demo](#demo)
- [Deployment](#deployment)

## Overview

A grocery list tracker webapp built using Flask and hosted on [Google Cloud Platform](https://cloud.google.com/). [Firebase](https://firebase.google.com/) integration is used for the management of user authentication; data storage is managed using [Google Datastore](https://cloud.google.com/datastore).

## Features

- Full Create, Read, Update, Delete functionality
- Dynamic ordering by importance and completed status
- Batch delete ability
- User activity indicator
- Responsive layout

## Technologies

- [Flask](https://flask.palletsprojects.com/en/2.2.x/)
- [Firebase](https://firebase.google.com/)
- [Google Cloud Platform](https://cloud.google.com/)
- [Google Datastore](https://cloud.google.com/datastore)
- [Tailwind CSS](https://tailwindcss.com/)
- [Font Awesome](https://fontawesome.com/)

## Demo

<img src="https://github.com/eoinlarkin/glist/raw/main/docs/glist_demo.gif"  height="400"/>

## Deployment

Prior to deployment it is necessary [install](https://cloud.google.com/sdk/docs/install) and [initialise](https://cloud.google.com/sdk/docs/initializing) the Google Cloud CLI.

The app instance can be created using the `gcloud app create` command.

### Locally:

1. Create an isolated Python enviromnet
   ```
   python3 -m venv env
   source env/bin/activate
   ```
2. Install app dependencies
   ```
   pip3 install -r requirements.txt
   ```
3. Run the application
   ```
   python3 main.py
   ```
4. Navigate to the application in your browser:
   ```
   http://localhost:8080
   ```

### Google Cloud Platform

1. Run the deployment command as follows:

   ```
   gcloud app deploy
   ```

2. View the cloud service:
   ```
   gcloud app browse
   ```
