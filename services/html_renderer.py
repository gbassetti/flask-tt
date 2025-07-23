from dataclasses import dataclass, field
import time
from services.application_state import ApplicationState
from services.config_loader import Config
from datetime import datetime

@dataclass
class HtmlRenderer:
    config: Config
    state: ApplicationState = field(default_factory=ApplicationState)

    def get_auth_link(self):
        if self.state.is_authorization_complete():
            return "javascript:void(0)"

        authorization_url = self.config.oauth.authorization_url
        client_id = self.config.oauth.client_id
        redirect_uri = self.config.server.get_redirect_uri()
        scopes = self.config.oauth.scopes.replace(" ", "%20")
        auth_url = (
            f"{authorization_url}?response_type=code"
            f"&client_id={client_id}"
            f"&redirect_uri={redirect_uri}"
            f"&scope={scopes}"
        )
        return auth_url
    
    def get_auth_code_value(self):
        #Get the authorization code
        if self.state.is_authorization_complete():
            return self.state.authorization_code_response.authorization_code
        return "Click the link to request authorization"

    def get_token_link(self):
        # Get HTML link to Token request endpoint 
        if not self.state.is_authorization_complete():
            return "javascript:void(0)"
        if not self.state.is_token_complete():
            return f'{self.config.server.get_local_url()}/get-token'
        if self.state.token_code_response.is_token_expired():
            return f'{self.config.server.get_local_url()}/refresh-token'
        return f'{self.config.server.get_local_url()}/refresh-token'
            
    def get_token_value(self):
        """Get Token value and expiration"""
        if not self.state.is_authorization_complete():
            return "App needs to be authorized to get a token"
        if not self.state.is_token_complete():
            return "Click the link to request a token"
        if self.state.token_code_response.is_token_expired():
            return "Link expired, refresh token"
        return self.state.token_code_response.access_token

    def get_token_expiration(self):
        """Get Token value and expiration"""
        if not self.state.is_authorization_complete():
            return ""
        if not self.state.is_token_complete():
            return ""        
        human_readable_expire = time.strftime(
            "%Y-%m-%d %H:%M:%S", 
            time.gmtime(self.state.token_code_response.access_token_expire)
        )
        return human_readable_expire
    
    def get_list_athletes_link(self):
        # Get a HTML Link to List Athletes endpoint
        if not self.state.is_authorization_complete():
            return "javascript:void(0)"
        if not self.state.is_token_complete():
            return "javascript:void(0)"
        if self.state.token_code_response.is_token_expired():
            return "javascript:void(0)"
        if not self.state.is_list_athletes_complete():
            return f'{self.config.server.get_local_url()}/get-athletes'
        return f'{self.config.server.get_local_url()}/get-athletes'
    
    def get_list_athletes_value(self):
        # Display result of Athletes request
        if not self.state.is_authorization_complete():
            return "App needs to be authorized to make a request"
        if not self.state.is_token_complete():
            return "App needs a token to make a request"
        if self.state.token_code_response.is_token_expired():
            return "Token Expired, Refresh Token."
        if not self.state.is_list_athletes_complete():
            return "Click the link to get athletes from TrainingPeaks"
        return self.state.list_athletes_response

    def get_list_athletes_timestamp(self):
        # Display timestamp of Athletes request
        if not self.state.is_authorization_complete():
            return ""
        if not self.state.is_token_complete():
            return ""
        if self.state.token_code_response.is_token_expired():
            return ""
        if not self.state.is_list_athletes_complete():
            return ""
        return datetime.now()
    
    def get_list_workouts_link(self):
        # Get a HTML Link to List Workouts endpoint
        if not self.state.is_authorization_complete():
            return "javascript:void(0)"
        if not self.state.is_token_complete():
            return "javascript:void(0)"
        if self.state.token_code_response.is_token_expired():
            return "javascript:void(0)"
        if not self.state.is_list_athletes_complete():
            return f'{self.config.server.get_local_url()}/get-workouts'
        return f'{self.config.server.get_local_url()}/get-workouts'
    
    def get_list_workouts_value(self):
        # Display result of Workouts request
        if not self.state.is_authorization_complete():
            return "App needs to be authorized to make a request"
        if not self.state.is_token_complete():
            return "App needs a token to make a request"
        if self.state.token_code_response.is_token_expired():
            return "Token Expired, Refresh Token."
        if not self.state.is_list_workouts_complete():
            return "Click the link to get workouts from TrainingPeaks"
        return self.state.list_workouts_response
    
    def get_list_workouts_timestamp(self):
        # Display timestamp of Workouts request
        if not self.state.is_authorization_complete():
            return ""
        if not self.state.is_token_complete():
            return ""
        if self.state.token_code_response.is_token_expired():
            return ""
        if not self.state.is_list_workouts_complete():
            return ""
        return datetime.now()

    def set_authorization_exception(self):
        self.state.exception_text = (
        "<h3>Authorization Failed.</h3>"
        "<p>"
        "Please double check credentials and make sure "
        "inbound traffic is permitted on the configured local port"
        "</p>"
    )

    def set_token_exception(self):
        self.state.exception_text = (
            "<h3>Token Generation Failed</h3>"
            "<p>"
            "Please double check the token_url and credentials in the config"
            "</p>"
        )

    def set_token_expired_exception(self):
        self.state.exception_text = (
            "<h3>Token Expired</h3>"
            "<p>"
            "Your Token has Expired, please refresh your token"
            "</p>"
        )

    def set_list_athlete_exception(self, status_code, body):
        self.state.exception_text = (
            f"<h3>List Athlete Request Failed</h3>"
            f"<p>Status: {status_code}</p>"
            f"<p>Body: {body}</p>"
        )
        
    def set_list_workouts_exception(self, status_code, body):
        self.state.exception_text = (
            f"<h3>List Workouts Request Failed</h3>"
            f"<p>Status: {status_code}</p>"
            f"<p>Body: {body}</p>"
        )

    def clear_exceptions(self):
        self.state.exception_text = ""

    def set_timestamp_now(self):
        self.state.timestamp_now = datetime.now()
    
    def update_context(self):
        context = {
            'exception_text': self.state.exception_text,
            'auth_code_request_status': self.state.authorization_code_request_status,
            'auth_code_response': self.get_auth_code_value(),
            'auth_link': self.get_auth_link(),
            'token_code_request_status': self.state.token_code_request_status,
            'token_value': self.state.token_code_response.access_token,
            'token_expiration': self.get_token_expiration(),
            'token_link': self.get_token_link(),
            'list_athletes_request_status': self.state.list_athletes_request_status,
            'list_athletes_value': self.get_list_athletes_value(),
            'list_athletes_link': self.get_list_athletes_link(),
            'list_athletes_timestamp': self.get_list_athletes_timestamp(),
            'date_seven_days': self.state.date_seven_days,
            'date_seven_days': self.state.date_yesterday,
            'list_workouts_request_status': self.state.list_workouts_request_status,
            'list_workouts_value': self.get_list_workouts_value(),
            'list_workouts_link': self.get_list_workouts_link(),
            'list_workouts_timestamp': self.get_list_workouts_timestamp()
        }
        return context
    
    '''
    def render(self):
        """Get HTML response based on current session state"""
        return f"""
            <!DOCTYPE html>
            <html>
                <head>
                    <title>Example OAuth 2.0 Authentication</title>
                    <style>
                        table {{
                            width: 100%;
                            max-width: 100%
                            border-collapse: collapse;
                            text-align: left;
                            font-family: Arial, sans-serif;
                            box-shadow: 0 2px 3px rgba(0,0,0,0.1);
                        }}
                        th, td {{
                            padding: 8px;
                            border: 1px solid #ddd;
                            word-break: break-word;
                        }}
                        th {{
                            background-color: #f2f2f2;
                            color: #333;
                        }}
                        tr:nth-child(even) {{
                            background-color: #f9f9f9;
                        }}
                        tr:hover {{
                            background-color: #f1f1f1;
                        }}
                        @media screen and (max-width: 600px) {{
                            table, th, td {{
                                font-size: 0.8em;
                            }}
                        }}
                    </style>
                </head>
                <body>
                    {self.state.exception_text}
                    <table>
                        <tr>
                            <th width="25%">Step</th>
                            <th width="25%">Status</th>
                            <th width="50%">Value</th>
                        </tr>
                        <tr>
                            <td>Authorization Code Request</td>
                            <td>{self.state.authorization_code_request_status}</td>
                            <td>{self.get_authorization_value()}</td>
                        </tr>
                        <tr>
                            <td>Token Request</td>
                            <td>{self.state.token_code_request_status}</td>
                            <td>{self.get_token_value()}</td>
                        </tr>
                        <tr>
                            <td>Get Athletes Request</td>
                            <td>{self.state.list_athletes_request_status}</td>
                            <td>{self.get_list_athletes_value()}</td>
                        </tr>
                        <tr>
                            <td>Get Workouts Request</td>
                            <td>{self.state.list_workouts_request_status}</td>
                            <td>Start Date <input type="date" name="startdate" value={self.state.date_yesterday}>
                            <br/>End Date <input type="date" name="enddate" value={self.state.date_yesterday}>
                            <br/>{self.get_list_workouts_value()}
                            <br/><button type="submit" class="btn btn-primary">Submit</button>
                            </td>
                        </tr>
                    </table>
                </body>
            </html>
        """
    '''