#!/usr/local/bin/python
# -*- coding: utf-8 -*-
from __future__ import print_function
import logging
import sqlite3
import re
import json
import datetime
__copyright__ = """MIT License

Copyright (c) 2019 Josh Dutterer

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE."""

__doc__ = "This is a sample generic parser to demonstrate using python to extract CAD data from a message"


def config():
    """
    Serves a dictionary describing how the main program 
    should behave and parse incoming data.
    """
    cfg = {
        "name": "alert"
    }
    cfg["preprocess"] = lambda text: str(text.decode("utf-8"))
    cfg["parsers"] = {
        "call_type": call_type_custom_function,
        "number": incident_number_custom_function,
        "location": location_custom_function,
        "equipment": equipment_custom_function,
        "remarks": remarks_custom_function,
        "time": time_custom_function
    }
    # time should never throw an error since we're getting the time from the system.

    # remarks and coordinates should never throw an error,
    # because they're icing on the cake;
    # we still want to alert the system if
    # all other functions parsed correctly

    # call_type, number, location, and equipment
    # should always throw any erors they encounter
    # up to the calling function, telling the main function
    # it could not grab all the necessary pieces
    # of data to represent an Incident
    return cfg


class ParsingError(Exception):
    """
    custom Exception
    """

    def __init__(self, parsing_property, data, parsing_error="Not specified"):
        self.timestamp = datetime.datetime.today().strftime('%Y-%m-%d %H:%M:%S')
        self.parsing_property = parsing_property
        self.data = data
        self.message = "{}\n\t'{}' function could not process the data:\n\t''{}''".format(
            self.timestamp, self.parsing_property, self.data)
        self.parsing_error = parsing_error

    def __str__(self):
        return self.message


def call_type_custom_function(data):
    """
    Get the incident type from the message, and return it as a string.
    """
    logging.getLogger()
    logging.basicConfig(filename='errors.log', level=logging.ERROR)

    call_type = r"Call Type (?P<call_type>[A-Z]+\s+\((?s).*\))"

    try:
        s = re.search(call_type, data, re.DOTALL)
        if(s):
            # if we found a match
            result = s.groupdict().get("call_type").strip()
            result = re.sub(r"\s+\)", ")", result)
        else:
            raise ParsingError("call_type", data, parsing_error="Insufficient regex")
        return result
    except Exception as err:
        # raise ParsingError("call_type", data, parsing_error=err)
        logging.exception(err)


def incident_number_custom_function(data):
    """
    Get the incident number from the message, and return it as a string.
    """
    logging.getLogger()
    logging.basicConfig(filename='errors.log', level=logging.ERROR)

    number = r"Incident No (?P<number>\d+)"
    # we use Regular Expressions and named groups to pull out key pieces of information
    try:
        s = re.search(number, data, re.DOTALL)
        if(s):
            # if we found a match
            result = s.groupdict().get("number").strip()
            # access the groups dictionary,
            # get the value for the key 'number',
            # and remove any leading or trailing whitespace
        else:
            raise ParsingError("number", data, parsing_error="Insufficient regex")
            # with parsing_error set as "Insufficient regex",
            # we'll know if our Regular Expression didn't return a match,
            # as opposed to any other errors
        return result
    except Exception as err:
        # Something unexpected happened in our custom function;
        # encapsulate the error in our custom Exception, so we'll be able to
        # easily distinguish this error in our custom parser, from any other
        # errors that may exist in our main program
        # raise ParsingError("number", data, parsing_error=err)
        logging.exception(err)


def coordinates_custom_function(query):
    """
    Dont worry about creating a function to look up coordinates yet.
    Suffice to say it should always return a 
    string with coordinates, or None.
    """
    return "39.6029,-77.0015"


def location_custom_function(data):
    """
    Location function should pull out the address, 
    then pass the appropriate components to the coordinates function
    to geocode the address. It then returns a tuple, where the first 
    element is the address in string form, and the second element is
    the coordinates in string form.
    """
    logging.getLogger()
    logging.basicConfig(filename='errors.log', level=logging.ERROR)

    location = r"Loc (?P<location>(?s).*(?=City))"
    try:
        s = re.search(location, data, re.DOTALL)
        if(s):
            # if we found a match
            result = s.groupdict().get("location").strip()
            # access the groups dictionary,
            # get the value for the key 'number',
            # and remove any leading or trailing whitespace
            query = "1100 Business Parkway S, Westminster, MD 21157"
            # you'd compile the addresses pieces into something
            # Google Maps API could parse
            coordinates = coordinates_custom_function(query)
            # then you'd call your function to make the
            # web request to the Google Maps API
            return result, coordinates
        else:
            raise ParsingError("location", data, parsing_error="Insufficient regex")
    except Exception as err:
        logging.exception(err)


def equipment_custom_function(data):
    """
    Pull the unit identifiers from the cad message. Each unit 
    signifies a single piece of equipment, such as F10 is
    fire truck for station 10, or A12 is ambulance for station 12.
    The value this function returns should be a list of strings, 
    where element in the list represents a single unit. 
    If no units are present, but its still a valid CAD message, 
    it should return an empty list.
    """
    logging.getLogger()
    logging.basicConfig(filename='errors.log', level=logging.ERROR)

    equipment = r"Units(?P<equipment>(\s(?s).*(?=\*\*\*\sPremise)))"

    try:
        s = re.search(equipment, data, re.DOTALL)
        if(s):
            # if we found a match
            result = s.groupdict().get("equipment").strip()
            result = result.split(", ")
            if result == [""]:
                result = []
        else:
            raise ParsingError("equipment", data, parsing_error="Insufficient regex")
        return result
    except Exception as err:    
        logging.exception(err)


def time_custom_function(data):
    """
    Current practice is to record the time we received the message, 
    rather than any particular timestamp that may or may not be in
    the message.
    """
    try:
        result = datetime.datetime.today().strftime("%Y-%m-%d %H:%M:%S")
        return result
    except Exception as err:
        raise ParsingError("time", data)


def remarks_custom_function(data):
    """
    Pull remarks, comments, and descriptive details from the message. 
    This function should return either None, or a string of all the 
    relvant details. This function and the coordinates function
    should never throw an error to the main program. 
    """
    remarks = r"Remarks (?P<remarks>(?s).*(?=Prty))"
    
    s = re.search(remarks, data, re.DOTALL)
    
    if(s):
        # if we found a match
        result = s.groupdict().get("remarks").strip()
        result = result.replace("\n", " ")
        return result


def get_data(filename):
    """
    Access the sqlite database <filename>, 
    and pull the cad messages from it for parsing.
    """
    data_list = []
    conn = None
    try:
        conn = sqlite3.connect('call_data_samples.db')
    except Error as e:
        print(e)
    cur = conn.cursor()
    cur.execute("SELECT data FROM cad")
    rows = cur.fetchall()
    for row in rows:
        data_list.append(row[0])
    return data_list


def parse_data(data):
    """
    Accept a list of strings, where each element is a CAD 
    message. Iterate over each message using the custom parsing functions
    for each piece of CAD data. Return a list of dictionaries containing 
    the key value pairs for each piece of data, and what was pulled from 
    the CAD message.
    """

    dict_list = []

    for msg in data:
        formatted_dict = {}
        # add number to dictionary
        number = incident_number_custom_function(msg)
        formatted_dict["number"] = number
        # add call_type to dictionary
        call_type = call_type_custom_function(msg)
        formatted_dict["call_type"] = call_type
        # add location and coordinates to dictionary
        location_tuple = location_custom_function(msg)
        if location_tuple is not None:
            # add location
            location = location_tuple[0]
            formatted_dict["location"] = location
            # add coordinates
            coordinates = location_tuple[1]
            formatted_dict["coordinates"] = coordinates
        else:
            location = None
        # add equipment(units) to dictionary
        equipment = equipment_custom_function(msg)
        formatted_dict["equipment"] = equipment
        # add remarks, if any, to dictionary
        remarks = remarks_custom_function(msg)
        if remarks is None:
            remarks = "None"
        formatted_dict["remarks"] = remarks
        # add time stamp to dictionary
        time = time_custom_function(msg)
        formatted_dict["time"] = time
        # add this dictionary to list of dictionaries
        if number and location and call_type and equipment is not None:
            dict_list.append(formatted_dict)
    
    return dict_list


def write_data(data, filename):
    """
    Accept a list of dictionaries, where each element is a the extracted
    pieces of CAD data from a single CAD message. Write the data to 
    a json file, <filename>, in the same format as what was
    provided in "call_data_samples.json"
    """
    # format into expected form as seen in call_data_samples file
    json_dict = {}
    json_dict['messages'] = data

    with open(filename, 'w') as outfile:
        json.dump(json_dict, outfile)

    return True


def main():
    data = get_data("call_data_samples.db")
    data = parse_data(data)
    data = write_data(data, "call_data_samples.json")


if __name__ == '__main__':
    main()
