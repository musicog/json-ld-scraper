# json-ld-scraper
BBC Radio 3 Early Music Show broadcast data scraper

Example python script to demonstrate how to turn JSON scraped from a public source (e.g. a BBC Radio programme resource) into linked data.

The BBC publishes JSON broadcast data about its programmes, including the BBC Radio 3 Early Music Show (http://www.bbc.co.uk/programmes/b006tn49/). 

We can take a given episode's URI (e.g. http://www.bbc.co.uk/programmes/b010xw37) and stick ".json" at the end (http://www.bbc.co.uk/programmes/b010xw37.json) to retrieve basic broadcast information. If we instead append "/segments.json" (http://www.bbc.co.uk/programmes/b010xw37/segments.json) we obtain a list of Segment Events corresponding loosely to the musical works featured on this particular episode, including information such as title, record label and record identifier, catalogue number, contributors (composer, performers, ...), etc. If we are lucky we also get a MusicBrainzID for the contributor(s), which can then be followed up via queries to MusicBrainz or LinkedBrainz. 

This script simply requests the most recent episode at the Early Music Show's episode listing page (http://www.bbc.co.uk/programmes/b006tn49/broadcasts/), encodes the episode and segment events JSON as linked data by supplying a hand-made JSON-LD context (more at http://json-ld.org/), stores the resulting triples in a graph, and then proceeds to the previous (i.e. next most recent) episode using information from the episode JSON. When it runs out of previous episodes, it stops, and serializes the graph into an RDF file using the Turtle format. 
