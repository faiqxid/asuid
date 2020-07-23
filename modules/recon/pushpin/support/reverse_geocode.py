import framework
# unique to module

class Module(framework.module):

    def __init__(self, params):
        framework.module.__init__(self, params)
        self.register_option('latitude', self.goptions['latitude']['value'], 'yes', self.goptions['latitude']['desc'])
        self.register_option('longitude', self.goptions['longitude']['value'], 'yes', self.goptions['longitude']['desc'])
        self.info = {
            'Name': 'Reverse Geocoder',
            'Author': 'Quentin Kaiser (contact@quentinkaiser.be)',
            'Description': 'Call the Google Maps API to obtain an address from coordinates.',
            'Comments': []
        }

    def module_run(self):
        lat = self.options['latitude']['value']
        lon = self.options['longitude']['value']
        self.verbose("Reverse geocoding (%f, %f)..." % (lat, lon))
        payload = {'latlng' : '%f,%f' % (lat,lon), 'sensor' : 'false'}
        url = 'https://maps.googleapis.com/maps/api/geocode/json'
        resp = self.request(url, payload=payload)
        # kill the module if nothing is returned
        if len(resp.json['results']) == 0:
            self.output('Unable to resolve an address for (%f, %f).' % (lat, lon))
            return
        # loop through and add results to a table
        tdata = []
        for result in resp.json['results']:
            tdata.append((result['geometry']['location_type'], result['formatted_address']))
        # output the table
        if tdata:
            tdata.insert(0, ('Type', 'Address'))
            self.table(tdata, header=True)
