"""All defined repositories for implementing data providers."""
from gator.data.repo import Repository, RepositoryRegistry
from gator.data.providers.uoft.utsg import UtsgArtsciTimetableDataset
from gator.models.timetable import Session

repo_registry = RepositoryRegistry()


@repo_registry.route('/timetable/uoft/artsci/:session_code')
def _utsg_artsci_timetable_repo(session_code: str) -> Repository:
    """Return a repository for the given session code.

    Args:
        session_code: The session code for the timetable to retrieve. If
            "latest", the latest session will be used.
    """
    if session_code == 'latest':
        session_code = UtsgArtsciTimetableDataset._get_latest_session().code

    # Validate the session code
    if not UtsgArtsciTimetableDataset._is_session_code_valid(session_code):
        raise ValueError('invalid session code!')
    else:
        session = Session.parse(session_code)
        # Build description
        desc = ('Timetable for the Faculty of Arts and Science at the University'
                ' of Toronto for the {} session.'.format(session.code))

        return Repository(
            [UtsgArtsciTimetableDataset(session_code)],
            slug=f'timetable-utsg-artsci-{session_code}',
            name='UTSG Arts and Science Timetable ({})'.format(
                session.human_str),
            description=desc
        )
