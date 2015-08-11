import requests
import bs4   
from pprint import pprint
from SPARQLWrapper import SPARQLWrapper, JSON
from rdflib import Graph, plugin, URIRef, Literal
from rdflib.parser import Parser
from rdflib.serializer import Serializer
#from rdflib.parser import Parser
#from rdflib.serializer import Serializer
import json
from time import sleep # be polite between BBC requests

def ldifySegments(segmentJson, episodePid):
    segmentJson["@context"] = { 
        "segment_events": "http://purl.org/dc/terms/hasPart",
        "@base": "http://www.bbc.co.uk/programmes/"
    }
    segmentJson["@id"] = episodePid
    for segmentEvent in segmentJson["segment_events"]:
        # segment event context and type
        segmentEvent["@context"] = {
            "pid": "@id",
            "po": "http://purl.org/ontology/po/",
            "dct": "http://purl.org/dc/terms/",
            "slobr": "http://slobr.linkedmusic.org/terms/",
            "@base": "http://www.bbc.co.uk/programmes/",
            "foaf": "http://xmlns.com/foaf/0.1/",
            "segment_events": "slobr:segment_events",
            "short_synopsis": "po:short_synopsis",
            "medium_synopsis": "po:medium_synopsis",
            "long_synopsis": "po:long_synopsis",
            "title": "dct:title",  
            "position": "slobr:position",
            "is_chapter": "slobr:is_chapter",
            "has_snippet": "slobr:has_snippet",
            "segment": "http://purl.org/dc/terms/hasPart"
        } 
        segmentEvent["@type"] = "slobr:SegmentEvents"

        # segment context and type
        segmentEvent["segment"]["@context"] = {
            "dct": "http://purl.org/dc/terms/",
            "mo": "http://purl.org/ontology/mo/",
            "pid": "@id",
            "duration": "po:duration",
            "record_id": "mo:recorded_as",
            "type": "slobr:segment_type",
            "artist": "slobr:artist", # nb: just a string, properly described as a contributor
            "track_title": "slobr:track_title", # nb: duplicated as "title"
            "track_title": "mo:track_number", 
            "publisher": "dct:publisher",
            "record_label": "mo:label",
            "release_title": "slobr:release_title",
            "catalogue_nunber": "dct:identifier", 
            "title": "dct:title",
            "short_synopsis": "po:short_synopsis",
            "medium_synopsis": "po:medium_synopsis",
            "long_synopsis": "po:long_synopsis",
            "contributions": "dct:contributor"
        }

        # restructure record_id and add context
        segmentEvent["segment"]["record_id"] = {
            "@context": { 
                "@base": "http://www.bbc.co.uk/music/records/",
                "record_id": "@id"
            },
            "record_id": segmentEvent["segment"]["record_id"]
        }

        # contributions context and type
        for contrib in segmentEvent["segment"]["contributions"]:
            contrib["@context"] = {
                "@base": "http://slobr.linkedmusic.org/contributors/",
                "mo": "http://purl.org/ontology/mo/",
                "pid": "@id", 
                "name": "foaf:name", 
                "role": "slobr:contributor_role",
                "musicbrainz_gid": "mo:musicbrainz_guid"
            }
            contrib["@type"] = "dct:Agent"

    return segmentJson

def ldifyEpisode(episodeJson):
    # episode context and type
    episodeJson['@context'] = {
        "pid" : "@id",
        "@base": "http://slobr.linkedmusic.org/",
        "slobr": "http://slobr.linkedmusic.org/terms/",
        "dct": "http://purl.org/dc/terms/",
        "po": "http://www.bbc.co.uk/ontologies/programmes/",
        "short_synopsis": "po:short_synopsis",
        "medium_synopsis": "po:medium_synopsis",
        "long_synopsis": "po:long_synopsis",
        "title": "dct:title", 
        "first_broadcast_date": "dct:date",
        "image": "dct:relation",
        "peers": "slobr:peers"
    }
    episodeJson["@type"] = "po:Episode"

    #episode image context and type
    episodeJson["image"]["@context"] = {
        "@base": "http://slobr.linkedmusic.org/bbcimages/",
        "pid": "@id"
    }

    # peer (prev/next episode) context and types:
    episodeJson["peers"]["@context"] = {
        "previous": "slobr:previousEpisode",
        "next": "slobr:nextEpisode"
    }
    for peer in ["previous", "next"]:
        if episodeJson["peers"][peer] is not None:
            episodeJson["peers"][peer]["@context"] = { "pid": "@id" }
            episodeJson["peers"][peer]["@type"] =  "po:Episode" 
    
    return episodeJson


def scrape(): 
    # create a new graph
    g = Graph()
    # grab page showing listing the latest month's episodes
    response = requests.get("http://www.bbc.co.uk/programmes/b006tn49/broadcasts/")
    soup = bs4.BeautifulSoup(response.text, "html.parser")
    # select the first episode listed (i.e. the most recent)
    episode = soup.select(".programme--episode")[0]
    # get the PID, i.e. the BBC identifier
    episodePid = episode.attrs.get("data-pid")
    while True: # loop until we run out of episodes
        # request the JSON for this episode
        episodeJson = requests.get("http://www.bbc.co.uk/programmes/" + episodePid + ".json").json()["programme"]
        # decorate the episode's JSON with JSON-LD contexts and types
        if episodeJson is None:
            break 
        episodeJson = ldifyEpisode(episodeJson)
        # eat the JSON-LD as RDF
        g.parse(data=json.dumps(episodeJson), format="json-ld")

        # request JSON for this episode's segments
        segmentPid = episodeJson["versions"][0]["pid"]
        segmentRes= requests.get("http://www.bbc.co.uk/programmes/{0}/segments.json".format(segmentPid))
        if segmentRes.text != "No segments":
            segmentJson = segmentRes.json()
            segmentJson = ldifySegments(segmentJson, episodePid)
            #eat the JSON-LD as RDF
            g.parse(data=json.dumps(segmentJson), format="json-ld")

        print "Finished {0} ({1})".format(episodePid, episodeJson["first_broadcast_date"])
        
        # prepare next iteration (i.e. look at next-most-recent episode)
        if(episodeJson["peers"]["previous"] is not None):
            episodePid = episodeJson["peers"]["previous"]["pid"]
            sleep(0.2) # be polite...
        else:
            # final episode
            break
    return g

if __name__ == "__main__":
    g = scrape()
    triples = open('EMS.ttl', 'w')
    triples.write(g.serialize(format = "turtle"))
    triples.close()

