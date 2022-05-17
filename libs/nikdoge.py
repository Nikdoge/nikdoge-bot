import datetime as dt
import json

def file_read_line_by_line(filename):
    #open file with list
    file = open(filename)
    list = [line.strip() for line in file]
    return list

def file_read_word_by_word(filename):
    #open file with words
    file = open(filename)
    list = []
    for line in file:
        line_list = line.split()
        list = list + line_list
    return list

def file_write(content,shortname=None,filename=None):
    if not filename:
        creation_time = dt.datetime.now().isoformat()
        if shortname: 
            filename = f'{creation_time}_{shortname}.txt'
        else:
            filename = f'{creation_time}.txt'
    file = open(filename,'w')
    file.write(content)
    file.close()
    return filename

#Must make possibility to add shortname after date for dymp_json and file_write
def dump_json(content,shortname=None,filename=None):
    if not filename:
        creation_time = dt.datetime.now().isoformat()
        if shortname: 
            filename = f'{creation_time}_{shortname}.json'
        else:
            filename = f'{creation_time}.json'
    file = open(filename,'w')
    file.write(json.dumps(content))
    file.close()
    return filename

def undump_json(filename):
    file = open(filename)
    content = json.loads(file.read())
    file.close()
    return content

class NpaLibError(Exception):
    """Base class for other exceptions"""
    pass
