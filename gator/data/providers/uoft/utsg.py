"""Data pipelines for UTSG datasets."""
import re
from typing import Optional, Union

import requests
from bs4 import BeautifulSoup


from gator.models.timetable import (
    Session, Organisation
)
from gator.data.pipeline.datasets import Dataset
from gator.data.pipeline.datasets.io import HttpResponseDataset
from gator.data.providers.common import TimetableDataset


class UtsgArtsciTimetableDataset(TimetableDataset):
    """A dataset for the Faculty of Arts and Science Timetable at the
    University of Toronto, St. George campus.

    Source: https://timetable.iit.artsci.utoronto.ca/api/

    Class Attributes:
        ROOT_URL: The root url for the API homepage.
        API_URL: The url for the API root endpoint.
        DEFAULT_HEADERS: A dict containing default headers used for API requests.

    Instance Attributes:
        session_code: The session code. Defaults to None, meaning the current session is used
            (as returned by the `sqrl.data.sources.ArtsciTimetableAPI.get_session_code` method).
    """

    ROOT_URL: str = 'https://timetable.iit.artsci.utoronto.ca'
    API_URL: str = f'{ROOT_URL}/api'
    DEFAULT_HEADERS: dict = {
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Methods': 'GET',
        'Access-Control-Allow-Headers': 'Content-Type',
        'Access-Control-Max-Age': '3600',
        # Emulate Gecko agent
        'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:52.0) Gecko/20100101 Firefox/52.0',
    }

    def __init__(self, session: Optional[Union[Session, str]] = None) -> None:
        """Initialize a new instance of the UtsgArtsciTimetableDataset class.

        Args:
            session: An optional session that can be supplied instead of the default.
                This can be an instance of Session or a string providing the session
                code.
        """
        super().__init__(session=session)
        self._organisations = self._get_all_organisations()

    @classmethod
    def _get_latest_session(cls, verify: bool = False) -> Session:
        """Return the session for the latest version of the Arts and Science timetable.
        Raise a ValueError if the session could not be found.

        Args:
            verify: Whether to verify the session code against the API.
        """
        request = requests.get(cls.ROOT_URL, cls.DEFAULT_HEADERS)
        soup = BeautifulSoup(request.content, 'html.parser')

        # The search button contains the session code
        search_button = soup.find(
            'input', {'id': 'searchButton', 'class': 'btnSearch'})

        SESSION_CODE_PATTERN = r'(?<=searchCourses\(\')\d{5}(?=\'\))'
        matches = re.findall(SESSION_CODE_PATTERN, search_button['onclick'])
        if len(matches) == 0:
            raise ValueError('failed to find session code!')

        session_code = matches[0]
        if verify and not cls._is_session_code_valid(session_code):
            raise ValueError('failed to find session code!')

        return Session.parse(session_code)

    @classmethod
    def _is_session_code_valid(cls, session_code: str) -> bool:
        """Verifies a session code against the API. Return whether the session code is valid."""
        # To verify the session code, we use it to find a course. The session code is valid if the
        # course is found. We assume that MAT137 will be in all sessions (which is a reasonable
        # assumption since it is a required course for a variety of majors, including computer science,
        # which has only been rising in popularity in the past few decades).
        SEARCH_COURSE = 'MAT137'
        data = requests.get(
            f'{cls.API_URL}/{session_code}/courses?code={SEARCH_COURSE}'
        ).json()
        # If we've found at least one course, the session code is valid
        return len(data) > 0

    @classmethod
    def _get_all_organisations(cls) -> Dataset:
        """Return a dataset containing all the course departments in the
        Faculty of Arts and Science as a list of sqrl.models.Organisation
        objects. Raise a ValueError if the organisations could not be
        retrieved. Note that this does NOT mutate the database.
        """
        dataset = HttpResponseDataset(f'{cls.API_URL}/orgs').json()
        # TODO: Add validation rules to the dataset pipeline
        # It might look something like this:
        # dataset = dataset.with_validation_rules(FunctionalValidator(
        #     lambda x: 'orgs' in x,
        #     'Failed to find organisations in response'
        # ))
        dataset = dataset.extract_key('orgs').kv_pairs().map(Organisation.parse)
