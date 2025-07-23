import os
import json
from flask import Flask, request, render_template, redirect, url_for
from threading import Thread
import pandas as pd
from datetime import datetime, timezone
from services.bigquery_api import BigQueryAPI
from services.config_loader import Config
from services.application_state import Status
from services.html_renderer import HtmlRenderer
from services.public_api import (
    AuthorizationCodeResponse,
    GetTokenRequest,
    GetTokenResponse,
    ListAthleteRequest,
    ListAthleteResponse,
    ListWorkoutsRequest,
    ListWorkoutsResponse,
    RefreshTokenRequest,
)
from datetime import datetime, timedelta

#Initialize Flask app
app = Flask(__name__)
app.secret_key = os.urandom(24)
config: Config = Config()
html_renderer = HtmlRenderer(config=config)
bq_api = BigQueryAPI()

# Google BigQuery authentication
#bq_credentials = service_account.Credentials.from_service_account_file('keys/spadotto-f1fdb-e96f694cf185.json')
#client = bigquery.Client(credentials=bq_credentials, project=bq_credentials.project_id)


# Function to get workouts from TP and post a status to the web app
def workouts_task(startdate, enddate):

    # Set initial variables
    current_workouts_df = bq_api.get_bq_table(config.bigquery_api.workouts_table_id)
    athlete_list, html_renderer.state.total_athletes = bq_api.get_athlete_ids(config.bigquery_api.athletes_table_id)
    html_renderer.state.task_status = 0
    new_data = []

    i = 1
    for id in athlete_list:
        print(f"Processing AthleteId:{id}, {i} out {html_renderer.state.total_athletes}")    
        html_renderer.state.current_athlete = i

        workouts_url = f"{config.public_api.list_workouts_endpoint}{id}/{startdate}/{enddate}"
        response: ListWorkoutsResponse = ListWorkoutsRequest().execute(
            workouts_url,
            html_renderer.state.token_code_response.access_token,
        )
        if response:
            rows = json.loads(response.data)
            new_data.extend(rows)
            print(f"Saved workouts for AthleteId: {id}")
        else:
            print(f"Error processing AthleteId {id}")
        
        #if i == 20: break # Stopping process early
        i = i + 1

    # Convert list of dicts to Dataframe and at timestamp
    df1 = pd.DataFrame(new_data)
    df1['updatedAt'] = datetime.now().replace(tzinfo=timezone.utc)

    # Concatenate Dataframes and remove duplicate entries (by Id), keeping the latest.
    new_workouts_df = pd.concat([current_workouts_df, df1])
    new_workouts_df = new_workouts_df.sort_values('updatedAt').drop_duplicates('Id',keep='last')

    # Upload to BQ database
    bq_api.upload_df_to_bq(new_workouts_df,config.bigquery_api.workouts_table_id)

    # Set success flag for display
    html_renderer.state.athletes_uploaded = "Athletes uploaded to database successfully."


@app.route("/", methods=['GET', 'POST'])
def index():
    """Single page of the Application"""

    # Handle the form submission for dates for workouts
    if request.method == "POST":
        start = request.form['startdate']
        end = request.form['enddate']
        return redirect(url_for("get_workouts", start=start, end=end))

    context = html_renderer.update_context()
    return render_template('index.html', **context)


@app.route("/callback")
def callback():
    """Handle callback from Authorization call"""
    if "code" not in request.args:
        html_renderer.state.authorization_code_request_status = Status.FAILURE.value
        html_renderer.set_authorization_exception()
    else:
        html_renderer.clear_exceptions()
        html_renderer.state.authorization_code_request_status = Status.SUCCESS.value
        html_renderer.state.authorization_code_response = AuthorizationCodeResponse(
            authorization_code=request.args.get("code")
        )
    return redirect("/")


@app.route("/get-token")
def get_token():
    #Use the Authorization Code to get an Access Token
    if not html_renderer.state.is_authorization_complete():
        return redirect ("/")
    
    if html_renderer.state.is_token_complete() and html_renderer.state.token_code_response.is_token_expired():
        html_renderer.state.token_code_request_status = Status.EXPIRED.value
        html_renderer.set_token_expired_exception()
        return redirect("/refresh-token")
    
    response: GetTokenResponse = GetTokenRequest(
        html_renderer.state.authorization_code_response.authorization_code,
        config.server.get_redirect_uri()
    ).execute(
        config.oauth.token_url, 
        config.oauth.client_id, 
        config.oauth.client_secret
    )

    if response:
        html_renderer.clear_exceptions()
        html_renderer.state.token_code_request_status = Status.SUCCESS.value
        html_renderer.state.token_code_response = response
    else:
        html_renderer.state.token_code_request_status = Status.FAILURE.value
        html_renderer.set_token_exception()
    
    return redirect("/")


@app.route("/refresh-token")
def refresh_token():
    # Use the Refresh Token to get a new Access Token
    if (
        not html_renderer.state.is_authorization_complete()
        or not html_renderer.state.is_token_complete()
    ):
        return redirect("/")

    response: GetTokenResponse = RefreshTokenRequest(
        html_renderer.state.token_code_response.refresh_token
    ).execute(config.oauth.token_url, config.oauth.client_id, config.oauth.client_secret)

    if response:
        html_renderer.clear_exceptions()
        html_renderer.state.token_code_request_status = Status.SUCCESS.value
        html_renderer.state.token_code_response = response
    else:
        html_renderer.state.token_code_request_status = Status.FAILURE.value
        html_renderer.set_token_exception()

    return redirect("/")


@app.route("/get-athletes")
def get_athletes():
    # Makes a GET request using the obtained token to fetch all athletes
    if (
        not html_renderer.state.is_authorization_complete()
        or not html_renderer.state.is_token_complete()
    ):
        return redirect("/")

    if html_renderer.state.token_code_response.is_token_expired():
        html_renderer.state.token_code_request_status = Status.EXPIRED.value
        html_renderer.set_token_expired_exception()
        return redirect("/")

    response: ListAthleteResponse = ListAthleteRequest().execute(
        config.public_api.list_athletes_endpoint,
        html_renderer.state.token_code_response.access_token,
    )

    if response:
        bq_api.upload_response_to_bq(response.data, config.bigquery_api.athletes_table_id)
        html_renderer.clear_exceptions()
        html_renderer.state.list_athletes_request_status = Status.SUCCESS.value
        #html_renderer.state.list_athletes_response = response
        html_renderer.state.list_athletes_response = Status.SUCCESS.value
    else:
        html_renderer.state.list_athletes_request_status = Status.FAILURE.value
        html_renderer.set_list_athlete_exception(response.status_code, response.message)
    return redirect("/")

@app.route("/get-workouts")
def get_workouts():
    # Makes a GET request using the obtained token to fetch workouts
    if (
        not html_renderer.state.is_authorization_complete()
        or not html_renderer.state.is_token_complete()
    ):
        return redirect("/")

    if html_renderer.state.token_code_response.is_token_expired():
        html_renderer.state.token_code_request_status = Status.EXPIRED.value
        html_renderer.set_token_expired_exception()
        return redirect("/")

    flag_success = True

    # Set the date range for the GET URL
    startdate = request.args.get('start')
    enddate = request.args.get('end')

    # Start workout processing function
    t1 = Thread(target=workouts_task(startdate=startdate, enddate=enddate))
    task_status = 12
    t1.start()
            
    if flag_success==True:
        html_renderer.clear_exceptions()
        html_renderer.state.list_workouts_request_status = Status.SUCCESS.value
        html_renderer.state.list_workouts_response = Status.SUCCESS.value
    else:
        html_renderer.state.list_workouts_request_status = Status.FAILURE.value
        #html_renderer.set_list_workouts_exception(response.status_code, response.message)
    return redirect("/")


@app.route('/status', methods=['GET'])
def getStatus():
  statusList = {'current':html_renderer.state.current_athlete,
                'total': html_renderer.state.total_athletes,
                'uploaded': html_renderer.state.athletes_uploaded
                }
  print(statusList)
  return json.dumps(statusList)


if __name__ == "__main__":
    app.run(host=config.server.host, port=config.server.local_port)
