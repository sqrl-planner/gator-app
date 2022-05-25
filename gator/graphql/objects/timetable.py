from typing import Any

import graphene
from graphene_mongo import MongoengineObjectType

from gator.models.timetable import (
    Organisation,
    Instructor,
    SectionMeeting,
    Section,
    Course,
)


class SectionMeetingObject(MongoengineObjectType):
    """A section meeting in the graphql schema."""

    class Meta:
        model = SectionMeeting


class InstructorObject(MongoengineObjectType):
    """An instructor in the graphql schema."""

    class Meta:
        model = Instructor


class SectionObject(MongoengineObjectType):
    """A section in the graphql schema."""

    class Meta:
        model = Section

    code = graphene.String()

    def resolve_code(self, info: graphene.ResolveInfo, **kwargs: Any) -> str:
        """Resolve the code of the section."""
        return self.code


class OrganisationObject(MongoengineObjectType):
    """An organisation in the graphql schema."""

    class Meta:
        model = Organisation


class OrganisationObjectConnection(graphene.relay.Connection):
    """A connection for the Organisation object."""

    class Meta:
        node = OrganisationObject


class CourseObject(MongoengineObjectType):
    """A course in the graphql schema."""

    class Meta:
        model = Course


class CourseObjectConnection(graphene.relay.Connection):
    """A connection for the Course object."""

    class Meta:
        node = CourseObject
