import graphene

from gator.graphql.schemas.timetable import TimetableQuery

# NOTE: To add a new query schema, make AppQuery inherit from your custom Query class.
class AppQuery(TimetableQuery, graphene.ObjectType):
    """All queries for the gator app."""

# NOTE: To add a new mutation schema, make AppMutation inherit from your custom Mutation class.
class AppMutation(graphene.ObjectType):
    """All mutations for the gator app."""


app_schema = graphene.Schema(query=AppQuery, mutation=AppMutation)
