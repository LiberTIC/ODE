from cornice.resource import resource, view

from ode.models import DBSession, Event
from ode.validation import EventSchema, EventCollectionSchema
from ode.resources.base import ResourceMixin


@resource(collection_path='/events', path='/events/{id}')
class EventResource(ResourceMixin):

    model = Event

    @view(schema=EventCollectionSchema)
    def collection_post(self):
        return ResourceMixin.collection_post(self)

    @view(schema=EventSchema)
    def put(self):
        return ResourceMixin.put(self)

    @view(accept='text/calendar', renderer='ical')
    @view(accept='application/json', renderer='json')
    def collection_get(self):
        """Get list of all events"""
        query = DBSession.query(Event).all()
        events = [event.to_dict() for event in query]
        return {'events': events}

    @view(accept='text/calendar', renderer='ical')
    @view(accept='application/json', renderer='json')
    def get(self):
        return ResourceMixin.get(self)
