import os


DUBLIN_CORE = ['title', 'id', 'group', 'contributer', 'subject', 'description', 'source', 'creator', 'publisher', 'format', 'date','owner','owner_type','type','language']
COMMON_MAPPINGS = {'method': 'source', 'date_created': 'date', 'creator_name': 'creator'}

def basicData(filepath):
    data = {}
    return commonData(data, filepath)

def commonData(data, filepath):

     """Sets default fields, creates coverage envelope, and maps common field names"""

     data['hubtype'] = 'idata-file'

     basename, ext = os.path.splitext(filepath)
     dirname,filename = os.path.split(filepath)
     data['id'] = filepath 
     data['identifier'] = filepath

     if 'title' not in data or data['title'] is None:
         data['title'] = filename

     if 'language' not in data: 
         data['language'] =  ext

     if 'format' not in data:
         data['format'] = ext

     if 'type' not in data:
         data['type'] = 'regular'

     data['owner_type'] = 'project'

     # determine project
     if filepath.startswith("/srv/idata/"):
         respath = filepath.split('/srv/idata/',1)[1]
         proj = respath.split('/',1)[0]
         data['group'] = proj
         data['owner'] = proj

     # make sure there is a url because the site breaks if there isn't one
     if 'url' not in data or data['url'] is None:
             data['url'] = 'http://129.114.16.188'

     # TODO: what should this be?
     if 'access_level' not in data or data['access_level'] is None:
          data['access_level'] = 'public'

     return data

def geoData(data,filepath):

     data = commonData(data, filepath)

     # if key exists and is not None, add it to coverage dictionary
     # always delete the entry from 'data' dictionary if it is present
     coverage = {}
     for key in ('lonmin', 'lonmax', 'latmax', 'latmin'): 
             if key in data:
                     if data[key] is not None:
                             coverage[key] = float(data[key])
     
     # if all four components were found, add the coverage field
     if len(coverage) == 4:
             data['coverage'] = 'ENVELOPE(%f,%f,%f,%f)' % (coverage['lonmin'], coverage['lonmax'],coverage['latmax'], coverage['latmin'])	
  
     # mappings common to all types of documents
     for key, value in data.items():
         if key in COMMON_MAPPINGS:
             data[COMMON_MAPPINGS[key]] = data.pop(key)
         elif data[key] == 'subdata':
             for subname, (subkey, subvalue) in data['subdata'].items():
                 if subkey in COMMON_MAPPPINGS:
                    data['subdata'][subname][COMMON_MAPPINGS[subkey]] = metadata['subdata'][subname].pop(subkey)
     return data
