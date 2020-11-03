"""
@ Author      : Daniel Palstra & Bram van Dartel & mendel129
@ Date        : 03/11/2020
@ Description : recycleapp.be Sensor - It queries https://www.recycleapp.be.
@ Notes:        https://github.com/mendel129/Unofficial-recycleapp.be-HASS
                Copy this file and place it in your
                "Home Assistant Config folder\custom_components\recycleapp\" folder.
"""
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.entity import Entity
from homeassistant.components.sensor import PLATFORM_SCHEMA
from homeassistant.const import (CONF_NAME)
from homeassistant.util import Throttle

import requests
from datetime import datetime, date, timedelta
import json
import argparse
import logging
import re
import voluptuous as vol

_LOGGER = logging.getLogger(__name__)

ICON = 'mdi:delete-empty'

TRASH_TYPES = [{1: "gft"}, {2: "PMD"}, {3: "huisvuil"}, {4: "grof vuil"}, {5: "Papier-karton"}]
SCAN_INTERVAL = timedelta(minutes=15)

DEFAULT_NAME = 'RecycleApp Sensor'
SENSOR_PREFIX = 'trash_'
CONST_POSTCODE = "postcode"
CONST_HUISNUMMER = "huisnummer"
CONST_STREET = "street"
CONST_STREETNR = "streetnr"
CONST_ZIPCODE = "zipcode"
CONST_CITY = "city"
CONST_DAYSINTHEFUTURE = "daysinthefuture"

CONF_CONSUMER = "recycleapp.be"
CONF_APPAPI="https://recycleapp.be/api/app/v1/"
# CONF_DAYSINFUTURE = 14
CONF_DAYSINFUTURE = 31
CONF_LANG='nl'
CONF_USERAGENT="Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:78.0) Gecko/20100101 Firefox/78.0"

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Optional(CONF_NAME, default=DEFAULT_NAME): cv.string,
    vol.Required(CONST_STREET): cv.string,
    vol.Required(CONST_STREETNR): cv.string,
    vol.Required(CONST_ZIPCODE): cv.string,
    vol.Required(CONST_CITY): cv.string,
    vol.Optional(CONST_DAYSINTHEFUTURE, default=31): cv.string,

})


def setup_platform(hass, config, add_devices, discovery_info=None):
    """Set up date afval sensor."""
    data = RecycleAppSchedule(TRASH_TYPES)

    devices = []
    for trash_type in TRASH_TYPES:
        #print(trash_type.values())
        for t in trash_type.values():
            devices.append(RecycleAppSensor(t, data))
    add_devices(devices)


class RecycleAppSensor(Entity):
    """Representation of a Sensor."""

    def __init__(self, name, data):
        """Initialize the sensor."""
        self._state = None
        self._name = name
        self.data = data

    @property
    def name(self):
        """Return the name of the sensor."""
        return SENSOR_PREFIX + self._name

    @property
    def state(self):
        """Return the state of the sensor."""
        return self._state

    @property
    def icon(self):
        """Return the icon to use in the frontend."""
        return ICON

    def update(self):
        """Fetch new state data for the sensor.

        This is the only method that should fetch new data for Home Assistant.
        """
        self.data.update()
        #print(self.data.data)
        for d in self.data.data:
            if d['name_type'] == self._name:
                self._state = d['pickup_date']


class RecycleAppSchedule(object):

    def __init__(self, trash_types):
        #self._url = url
        self._trash_types = trash_types
        self.data = None

    @Throttle(SCAN_INTERVAL)
    def update(self):
        #response = urlopen(self._url)
        #string = response.read().decode('utf-8')
        #json_obj = json.loads(string)
        #today = datetime.date.today().strftime("%Y-%m-%d")
        tschedule = []
		
        #this is a random test address - no association to me whatsoever
        CONF_STREET= "August Van de Wielelei"
        CONF_STREETNR= "253"
        CONF_ZIPCODE= "2100"
        CONF_CITY= "Deurne"

        CONF_CONSUMER = "recycleapp.be"
        CONF_APPAPI="https://recycleapp.be/api/app/v1/"
        CONF_DAYSINFUTURE = 31
        CONF_LANG='nl'
        CONF_USERAGENT="Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:78.0) Gecko/20100101 Firefox/78.0"

        today=datetime.today().strftime("%Y-%m-%d")
        future=str((date.today() + timedelta(days=CONF_DAYSINFUTURE)).strftime("%Y-%m-%d"))

        #fetch the session token
        headers = {"User-Agent": CONF_USERAGENT}
        javascriptlocation=re.search(r'/static/js/main.*.chunk.js', str(requests.get("https://www.recycleapp.be", headers=headers, timeout=10).content))
        tokendata=re.search(r'var n="\w+"', str((requests.get("https://www.recycleapp.be"+javascriptlocation.group(0), headers=headers, timeout=10)).content))
        token=tokendata.group(0)[7:len(tokendata.group(0))-1]
        headers = {"x-secret": token, "x-consumer": CONF_CONSUMER, "User-Agent": CONF_USERAGENT}
        request = requests.get(CONF_APPAPI+"access-token", headers=headers, timeout=10)
        token=request.json()['accessToken']

        #find city id
        headers = {"Authorization": token, "x-consumer": CONF_CONSUMER, "User-Agent": CONF_USERAGENT}
        zips = requests.get(CONF_APPAPI+"zipcodes?q="+CONF_ZIPCODE, headers=headers, timeout=10)
        data=zips.json()['items'][0]
        cityid=""
        for name in data['names']:
           if name[CONF_LANG] == CONF_CITY:
              cityid=data['id']
        
        #find street id - todo make case insensitive
        params = {"q":CONF_STREET, "zipcodes":cityid}
        street = requests.post(CONF_APPAPI+"streets", params=params, headers=headers, timeout=10)
        data=street.json()['items'][0]
        streetid=""
        #todo, iterate over multiple found streets and check if in correct city
        if data['names'][CONF_LANG] == CONF_STREET:
           streetid=data['id']
   
        #finally get the data - todo make case insensitive
        today=datetime.today().strftime("%Y-%m-%d")
        future=str((date.today() + timedelta(days=CONF_DAYSINFUTURE)).strftime("%Y-%m-%d"))
        headers = {"Authorization": token, "x-consumer": CONF_CONSUMER, "User-Agent": CONF_USERAGENT}
        finalurl=CONF_APPAPI+'collections/?zipcodeId='+cityid+'&streetId='+streetid+'&houseNumber='+CONF_STREETNR+'&fromDate='+today+'&untilDate='+future+'&size=100'
        request = requests.get(finalurl, headers=headers, timeout=10)
        json_obj=request.json()['items']

        for name in TRASH_TYPES:
            for item in json_obj:
                    if item['fraction']['name']['nl'] in name.values():
                        trash = {}
                        #trash['shortcode'] = (next(iter(name.values())))
                        trash['name_type'] = item['fraction']['name']['nl']
                        #trash['pickup_date'] = (str(datetime.strptime(item['timestamp'], "%Y-%m-%dT%H:%M:%S.%fZ")))
                        trash['pickup_date'] = (datetime.strftime((datetime.strptime(item['timestamp'], "%Y-%m-%dT%H:%M:%S.%fZ")), '%Y-%m-%d'))
                        #trash['pickup_date'] = (str(datetime.strptime(item['date'], "%Y-%m-%d") + datetime.timedelta(days=0)))
                        tschedule.append(trash)
                        self.data = tschedule
                        break
