"""Module providing Enum for call status"""

from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime, timedelta

from services.public_api import (
    AuthorizationCodeResponse,
    GetTokenResponse,
    ListAthleteResponse,
    ListWorkoutsResponse,
)


class Status(Enum):
    """Enum object for call status"""

    NOT_RUN = "Not Run"
    SUCCESS = "Success"
    FAILURE = "Failure"
    EXPIRED = "Expired"
    RUNNING = "Running"


@dataclass
class ApplicationState:
    # Authorization Code
    authorization_code_request_status: str = Status.NOT_RUN.value
    authorization_code_response: AuthorizationCodeResponse = field(
        default_factory=AuthorizationCodeResponse
    )
    # Token Code
    token_code_request_status: str = Status.NOT_RUN.value
    token_code_response: GetTokenResponse = field(default_factory=GetTokenResponse)
    # List Athletes
    list_athletes_request_status: str = Status.NOT_RUN.value
    list_athletes_response: str =  Status.NOT_RUN.value
    #list_athletes_response: ListAthleteResponse = field(
    #    default_factory=ListAthleteResponse
    #)
    # List Workouts
    list_workouts_request_status: str = Status.NOT_RUN.value
    list_workouts_response: str = Status.NOT_RUN.value
    #list_workouts_response: ListWorkoutsResponse = field(
    #    default_factory=ListWorkoutsResponse
    #)
    # Exception
    exception_text: str = None

    # Dates for range
    date_seven_days: str = (datetime.today() - timedelta(8)).strftime('%Y-%m-%d') 
    date_yesterday: str = (datetime.today() - timedelta(1)).strftime('%Y-%m-%d')
    
    # Number of athletes and workouts in lists
    count_athletes: int = None
    count_workouts: int = None

    # Progress status variables
    current_athlete: int = 0
    total_athletes: int = 0
    task_status: int = 0
    athletes_uploaded: str = None

    def is_authorization_complete(self) -> bool:
        return self.authorization_code_request_status == Status.SUCCESS.value

    def is_token_complete(self) -> bool:
        return self.token_code_request_status == Status.SUCCESS.value

    def is_list_athletes_complete(self) -> bool:
        return self.list_athletes_request_status == Status.SUCCESS.value

    def is_list_workouts_complete(self) -> bool:
        return self.list_workouts_request_status == Status.SUCCESS.value
