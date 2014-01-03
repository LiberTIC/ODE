# -*- encoding: utf-8 -*-
from unittest import TestCase
from mock import Mock, patch

from ode.models import Event, DBSession
from ode.tests.event import TestEventMixin
from ode.harvesting import harvest


valid_icalendar = u"""
BEGIN:VCALENDAR
VERSION:2.0
PRODID:-//AgendaDuLibre.org
X-WR-CALNAME:Agenda du Libre - tag toulibre
X-WR-TIMEZONE:Europe/Paris
CALSCALE:GREGORIAN
X-WR-CALDESC:L'Agenda des évènements autour du Libre, tag toulibre
BEGIN:VEVENT
DTSTART;TZID=Europe/Paris:20121124T110000
DTEND;TZID=Europe/Paris:20121125T170000
UID:1234
SUMMARY:Capitole du Libre
URL:http://www.agendadulibre.org/showevent.php?id=7064
DESCRIPTION:Un évènement de l'Agenda du Libre
LOCATION:Toulouse
END:VEVENT
END:VCALENDAR
"""

start_time_missing = u"""
BEGIN:VCALENDAR
VERSION:2.0
PRODID:-//AgendaDuLibre.org
X-WR-CALNAME:Agenda du Libre - tag toulibre
X-WR-TIMEZONE:Europe/Paris
CALSCALE:GREGORIAN
X-WR-CALDESC:L'Agenda des évènements autour du Libre, tag toulibre
BEGIN:VEVENT
DTEND;TZID=Europe/Paris:20121125T170000
UID:1234
SUMMARY:Capitole du Libre
URL:http://www.agendadulibre.org/showevent.php?id=7064
DESCRIPTION:Un évènement de l'Agenda du Libre
LOCATION:Toulouse
END:VEVENT
END:VCALENDAR
"""


valid_json = (
    u'{"collection": {"href": "http://localhost:6543/v1/events", "items": [{"h'
    u'ref": "http://localhost:6543/v1/events/4c81f072630e11e3953c5c260a0e691e%'
    u'40example.com", "data": [{"name": "id", "value": "4c81f072630e11e3953c5c'
    u'260a0e691e@example.com"}, {"name": "description", "value": "Description"'
    u'}, {"name": "performers", "value": "artiste1, artiste2, artiste3"}, {"na'
    u'me": "press_url", "value": "http://presse"}, {"name": "price_information'
    u'", "value": "tarif"}, {"name": "target", "value": "public"}, {"name": "t'
    u'itle", "value": "Test medias"}, {"name": "start_time", "value": "2013-12'
    u'-12T00:00:00"}, {"name": "end_time", "value": "2013-12-28T00:00:00"}, {"'
    u'name": "publication_start", "value": "2013-12-12T00:00:00"}, {"name": "p'
    u'ublication_end", "value": "2013-12-28T00:00:00"}, {"name": "press_contac'
    u't_email", "value": "aaa@aaa.aa"}, {"name": "press_contact_name", "value"'
    u': "nom presse"}, {"name": "press_contact_phone_number", "value": "teleph'
    u'one presse"}, {"name": "ticket_contact_email", "value": "aaa@aaa.aa"}, {'
    u'"name": "ticket_contact_name", "value": "nom billetterie"}, {"name": "ti'
    u'cket_contact_phone_number", "value": "telephone billetterie"}, {"name": '
    u'"location_name", "value": "Nom du lieu"}, {"name": "location_address", "'
    u'value": "Adresse du lieu"}, {"name": "location_post_code", "value": "Cod'
    u'e postal"}, {"name": "location_capacity", "value": "capacite"}, {"name":'
    u'"location_town", "value": "Ville"}, {"name": "location_country", "value"'
    u': "Pays"}, {"name": "tags", "value": ["tag1", "tag2", "tag3"]}, {"name":'
    u'"categories", "value": ["category1", "category2"]}, {"name": "images", "'
    u'value": [{"url": "http://photo", "license": "CC BY"}, {"url": "http://ph'
    u'oto2", "license": "CC BY"}]}, {"name": "videos", "value": [{"url": "http'
    u'://video", "license": "CC BY"}]}, {"name": "sounds", "value": [{"url": "'
    u'http://audio", "license": "CC BY"}]}]}], "current_count": 1, "version": '
    u'"1.0", "total_count": 1}}'
    )


class TestHarvesting(TestEventMixin, TestCase):

    def setup_requests_mock(self, content_type='text/calendar',
                            icalendar_data=valid_icalendar):
        requests_patcher = patch('ode.harvesting.requests')
        self.mock_requests = requests_patcher.start()
        self.addCleanup(requests_patcher.stop)
        self.mock_requests.get.return_value = Mock(
            status_code=200,
            content_type=content_type,
            text=icalendar_data,
        )

    def test_fetch_data_from_source(self):
        self.setup_requests_mock()
        source = self.make_source()
        harvest()
        self.mock_requests.get.assert_called_with(source.url)
        event = DBSession.query(Event).one()
        self.assertEqual(event.title, u"Capitole du Libre")
        self.assertEqual(event.url,
                         u"http://www.agendadulibre.org/showevent.php?id=7064")
        self.assertEqual(event.description,
                         u"Un évènement de l'Agenda du Libre")

    def test_fetch_json_data_from_source(self):
        self.setup_requests_mock(content_type='text/json',
                                 icalendar_data=valid_json)
        source = self.make_source()
        harvest()
        self.mock_requests.get.assert_called_with(source.url)
        event = DBSession.query(Event).one()
        self.assertEqual(event.title, u"Test medias")
        self.assertEqual(event.description,
                         u"Description")

    def test_duplicate_is_changed(self):
        self.create_event(title=u'Existing event', id=u'1234@example.com')
        DBSession.flush()
        self.setup_requests_mock()
        source = self.make_source()
        harvest()
        self.mock_requests.get.assert_called_with(source.url)
        event = DBSession.query(Event).one()
        self.assertEqual(event.title, u"Capitole du Libre")

    def test_invalid_calendar(self):
        self.setup_requests_mock(icalendar_data=start_time_missing)
        source = self.make_source()
        harvest()
        self.mock_requests.get.assert_called_with(source.url)
        self.assertEqual(DBSession.query(Event).count(), 0)
