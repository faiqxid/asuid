import framework
import __builtin__
# unique to module
import urllib
import re
import time
import random
import hashlib

class Module(framework.module):

    def __init__(self, params):
        framework.module.__init__(self, params)
        self.options = {
                        'domain': self.goptions['domain']
                        }
        self.info = {
                     'Name': 'Netcraft Hostname Enumerator',
                     'Author': 'thrapt (thrapt@gmail.com)',
                     'Description': 'Harvests hosts from Netcraft.com. This module updates the \'hosts\' table of the database with the results.',
                     'Comments': []
                     }

    def do_run(self, params):
        self.get_hosts()
    
    def get_hosts(self):
        domain = self.options['domain']
        verbose = self.goptions['verbose']
        url = 'http://searchdns.netcraft.com/'        
        payload = {'restriction': 'site+ends+with', 'host': domain}
        pattern = '<td align\=\"left\">\s*<a href=\"http://(.*?)/"'
        subs = []
        cnt = 0
        cookies = {}
        # control variables
        New = True
        # execute search engine queries and scrape results storing subdomains in a list
        # loop until no Next Page is available
        while New:
            content = None
            if verbose: self.output('URL: %s?%s' % (url, urllib.urlencode(payload)))

            # process and store cookies
            if len(cookies) == 0:
                try: content = self.request(url, payload=payload)
                except KeyboardInterrupt:
                    print ''
                except Exception as e:
                    self.error(e.__str__())
                if not content: break

                # this was taken from the netcraft page's JavaScript, no need to use big parsers just for that
                # grab the cookie sent by the server, hash it and send the response
                cookie = content.headers['set-cookie']
                # gets the value of netcraft_js_verification_challenge...
                challenge_token = (cookie.split('=')[1].split(';')[0])
                # ... hash it and store as cookie
                response = hashlib.sha1(urllib.unquote(challenge_token))
                cookies = {
                           'netcraft_js_verification_response': '%s' % response.hexdigest(),
                           'netcraft_js_verification_challenge': '%s' % challenge_token,
                           'path': '/'
                          }

            # Now we can request the page again
            try: content = self.request(url, payload=payload, cookies=cookies)
            except KeyboardInterrupt:
                print ''
            except Exception as e:
                self.error(e.__str__())

            content = content.text

            sites = re.findall(pattern, content)
            # create a unique list
            sites = list(set(sites))
            
            # add subdomain to list if not already exists
            for site in sites:
                if site not in subs:
                    subs.append(site)
                    self.output('%s' % (site))
                    cnt += self.add_host(site)
            
            # Verifies if there's more pages to look while grabbing the correct 
            # values for our payload...
            link = re.findall(r'(\blast\=\b|\bfrom\=\b)(.*?)&', content)
            if not link:
                New = False
                break
            else:
                payload['last'] = link[0][1]
                payload['from'] = link[1][1]
                if verbose: self.output('Next page available! Requesting again...' )

            # sleep script to avoid lock-out
            if verbose: self.output('Sleeping to Avoid Lock-out...')
            try: time.sleep(random.randint(5,15))
            except KeyboardInterrupt:
                print ''
                break
            
        if verbose: self.output('Final Query String: %s?%s' % (url, urllib.urlencode(payload)))
        self.output('%d total hosts found.' % (len(subs)))
        if cnt: self.alert('%d NEW hosts found!' % (cnt))