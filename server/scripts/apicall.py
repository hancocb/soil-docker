#First, we import the task id provided from the node script
############################################################################
import sys
taskID = sys.argv[1]
#taskID = 'c5a9043a-7424-417f-bd08-20b463cf3564'


#Maybe return something to the script, so it knows things are running?
############################################################################
#print('Task : ' + taskID)


#Get and prep the data from the server
############################################################################
from pymongo import MongoClient
import os

client = MongoClient(os.environ.get('MONGO_URI'))
db = client['soil']
tasks = db.tasks
task = tasks.find_one({'id': taskID})
data = {
  'points': task['points'],  
  'boundary': task['boundary'],
  'id': task['id']  
}

#Convert polygon coords to float
for fIndex, feature in enumerate(data['boundary']['features']):
  data['boundary']['features'][fIndex]['properties'] = {}
  for lrIndex, linearRing in enumerate(feature['geometry']['coordinates']):
    for vIndex, vertex in enumerate(linearRing):
      for cIndex, coordinate in enumerate(vertex):
        data['boundary']['features'][fIndex]['geometry']['coordinates'][lrIndex][vIndex][cIndex] = float(coordinate)

#Convert point coords to float
for fIndex, feature in enumerate(data['points']['features']):
  for cIndex, coordinate in enumerate(feature['geometry']['coordinates']):
    data['points']['features'][fIndex]['geometry']['coordinates'][cIndex] = float(coordinate)

#Convert point property of interest to float
for fIndex, feature in enumerate(data['points']['features']):
  data['points']['features'][fIndex]['properties']['value'] = float(data['points']['features'][fIndex]['properties']['value'])


#Push to the script
############################################################################
import subprocess
import os
import shutil
#Make the process directory
subprocess.call('mkdir ', shell=True)
subprocess.call('mkdir ' + data['id'] + '/', shell=True)
subprocess.call('mkdir ' + data['id'] + '/rootdata', shell=True)
subprocess.call('mkdir ' + data['id'] + '/topo', shell=True)
subprocess.call('mkdir ' + data['id'] + '/individuals', shell=True)
subprocess.call('mkdir ' + data['id'] + '/buffers', shell=True)
subprocess.call('mkdir ' + data['id'] + '/topo/curvatures', shell=True)

import root
response = root.validate_predict(data)

#Update the task document
if response['status'] == 400:
  task['status'] = 'invalid input'
  task['message'] = response['message']

elif response['status'] == 500:
  task['status'] = 'server error'
  task['message'] = response['message']

elif response['status'] == 200:
  task['status'] = 'complete'
  task['message'] = response['message']
  #task['scores'] = response['scores']
  task['bounds'] = response['bounds']
  task['jpgPath'] = task['id'] + '.jpg'
  task['tifPath'] = task['id'] + '.tif'

else:
  task['status'] = 'server error'
  task['message'] = 'server error'
  
tasks.update_one({'id': taskID}, {"$set": task}, upsert=False)
print(response['status'])

#Remove process directory
if os.path.isdir(data['id']):
  shutil.rmtree(data['id'])



