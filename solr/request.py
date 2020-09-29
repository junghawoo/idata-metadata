import sys, requests, json, os
import xml.etree.ElementTree as ET	
import xml.dom.minidom as minidom

SOLR_CORE_URL = str(os.getenv('SOLR_URL'))

# all strings except for title should be interpretted as text_general (*_t) or multivalue text_general (*_txt)
DYNAMIC = { str: '_t',  int: '_i', float: '_f'} 
MULTIVALUE = { str: '_txt', int: '_is', float: '_fs'} 

# all the fields that aren't dynamic
DUB_CORE = ['coverage', 'url', 'hubtype', 'access_level',  'owner', 'owner_type', 'id', 'title', 'description', 'subject', 'contributor', 'publisher', 'id', 'format', 'type', 'source', 'creator', 'language']
GEO_FIELDS = ['northlimit', 'southlimit', 'eastlimit', 'westlimit', 'latmin', 'latmax', 'lonmin', 'lonmax', 'xsize', 'ysize']

def newFile(data):
    """Takes a metadata dictionary, creates a Solr-friendly XML file, and posts the request.

    Parameters: 
       data (dict): A multilevel dictionary containing file metadata
    """
    
    # build xml
    root = ET.Element("add")
    doc = ET.SubElement(root, "doc")
    for fieldname, value in data.items():
            if fieldname == 'subdata':
                for subname, subdata in value.items():
                    for subfield, subvalue in subdata.items():
                        __add_element(doc, subfield, subvalue, subname) 
            else:
                __add_element(doc, fieldname, value) 
                
    # generate binary string containing xml data 
    xml_byte_string = ET.tostring(root, encoding='utf-8')

    # debug: generate file containing xml data just to examine it for now
    # pretty_string = minidom.parseString(xml_byte_string).toprettyxml(indent='\t')
    # print(pretty_string)
    
    __post_request(xml_byte_string)


def deleteFile(filename):

    root = ET.Element("delete")
    doc = ET.SubElement(root, "id").text = filename
    xml_byte_string = ET.tostring(root, encoding='utf-8')
    __post_request(xml_byte_string)


def renameFile(oldname, newname):

    request_str = SOLR_CORE_URL + '/get?id=' + oldname
    print(request_str)
    r = requests.get(request_str)
    doc_dict = r.json()['doc']
    print(doc_dict)
    for field in ('_version_', 'timestamp'):
       if field in doc_dict:
          doc_dict.pop(field)
    doc_dict['id'] = newname
    deleteFile(oldname)
    newFile(doc_dict)

def __add_element(doc, fieldname, value, subname=None):
    
    # add prefix if needed
    if not subname:
                if fieldname in GEO_FIELDS:
                        name = 'geo_' + fieldname
                else:
                        name = fieldname
    else:
        name = subname + '_' + fieldname 
    

    # add the appropriate postfix
    if subname or fieldname not in DUB_CORE:
         if isinstance(value, list):
             name = name +  MULTIVALUE.get(type(value[0]))
             for element in value:
                 ET.SubElement(doc, "field", name=name).text = str(element)
         else: 
             name = name + DYNAMIC.get(type(value))
             ET.SubElement(doc, "field", name=name).text = str(value)
    else:
        ET.SubElement(doc, "field", name=name).text = str(value)
   
    
def __post_request(xml_byte_string):	
        
    headers={'Content-Type' : 'text/xml'}
    #TODO: change commit setting to something reasonable 
    params={'commit': 'true'}
    r = requests.post(SOLR_CORE_URL + "/update", data=xml_byte_string, headers=headers, params=params) 

    # debug: remove me
    with open("/tmp/messages.txt","a+") as logfile:
        logfile.write(r.text)

    # throw an error if indexing was unsuccessful
    r.raise_for_status()
