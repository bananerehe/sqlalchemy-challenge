## Import
import numpy as np
import datetime as dt
import re

from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import Session
from sqlalchemy import create_engine, func
from sqlalchemy.sql import exists

from flask import Flask, jsonify

## Create Engine & Database
engine = create_engine("sqlite:///Resources/hawaii.sqlite")
Base = automap_base()
Base.prepare(engine, reflect=True)

## Save references to the measurement and stations tables
Measurement = Base.classes.measurement
Stations = Base.classes.station

## Create session
session = Session(engine)

## Flask
app = Flask(__name__)

## Routes
@app.route("/")
def welcome():
    """List all available API routes."""
    return (
        f"Available Routes:<br/>"
        f"/api/v1.0/precipitation<br/>"
        f"/api/v1.0/stations<br/>"
        f"/api/v1.0/tobs<br/>"
        f"/api/v1.0/start (enter as YYYY-MM-DD)<br/>"
        f"/api/v1.0/start/end (enter as YYYY-MM-DD/YYYY-MM-DD)"
    )
    
## Precipitation API
@app.route("/api/v1.0/precipitation") 
def precipitation():
    session = Session(engine)
    results = (session.query(Measurement.date, Measurement.tobs)
                      .order_by(Measurement.date))
    
    precipitation_date_tobs = []
    for each_row in results:
        dt_dict = {}
        dt_dict["date"] = each_row.date
        dt_dict["tobs"] = each_row.tobs
        precipitation_date_tobs.append(dt_dict)

    return jsonify(precipitation_date_tobs)

## Stations API
def stations():
    session = Session(engine)
    results = session.query(Stations.name).all()
    station_details = list(np.ravel(results))
    return jsonify(station_details)

## TOBS API
@app.route("/api/v1.0/tobs") 
def tobs():
    session = Session(engine)
    latest_date = (session.query(Measurement.date)
                          .order_by(Measurement.date
                          .desc())
                          .first())
    
    latest_date_str = str(latest_date)
    latest_date_str = re.sub("'|,", "",latest_date_str)
    latest_date_obj = dt.datetime.strptime(latest_date_str, '(%Y-%m-%d)')
    query_start_date = dt.date(latest_date_obj.year, latest_date_obj.month, latest_date_obj.day) - dt.timedelta(days=366)
     
    q_station_list = (session.query(Measurement.station, func.count(Measurement.station))
                             .group_by(Measurement.station)
                             .order_by(func.count(Measurement.station).desc())
                             .all())
    
    station_hno = q_station_list[0][0]
    print(station_hno)


    results = (session.query(Measurement.station, Measurement.date, Measurement.tobs)
                      .filter(Measurement.date >= query_start_date)
                      .filter(Measurement.station == station_hno)
                      .all())

    tobs_list = []
    for result in results:
        line = {}
        line["Date"] = result[1]
        line["Station"] = result[0]
        line["Temperature"] = int(result[2])
        tobs_list.append(line)

    return jsonify(tobs_list)

## Filter APIs
@app.route("/api/v1.0/<start>")
def start_only(start):
    session = Session(engine)

    date_range_max = session.query(Measurement.date).order_by(Measurement.date.desc()).first()
    date_range_max_str = str(date_range_max)
    date_range_max_str = re.sub("'|,", "",date_range_max_str)
    print (date_range_max_str)

    date_range_min = session.query(Measurement.date).first()
    date_range_min_str = str(date_range_min)
    date_range_min_str = re.sub("'|,", "",date_range_min_str)
    print (date_range_min_str)


    valid_entry = session.query(exists().where(Measurement.date == start)).scalar()
 
    if valid_entry:

    	results = (session.query(func.min(Measurement.tobs)
    				 ,func.avg(Measurement.tobs)
    				 ,func.max(Measurement.tobs))
    				 	  .filter(Measurement.date >= start).all())

    	tmin =results[0][0]
    	tavg ='{0:.4}'.format(results[0][1])
    	tmax =results[0][2]
    
    	result_printout =( ['Entered Start Date: ' + start,
    						'The lowest Temperature was: '  + str(tmin) + ' F',
    						'The average Temperature was: ' + str(tavg) + ' F',
    						'The highest Temperature was: ' + str(tmax) + ' F'])
    	return jsonify(result_printout)

    return jsonify({"error": f"Input Date {start} not valid. Date Range is {date_range_min_str} to {date_range_max_str}"}), 404
   

@app.route("/api/v1.0/<start>/<end>")
def start_end(start, end):
    session = Session(engine)

    date_range_max = session.query(Measurement.date).order_by(Measurement.date.desc()).first()
    date_range_max_str = str(date_range_max)
    date_range_max_str = re.sub("'|,", "",date_range_max_str)
    print (date_range_max_str)

    date_range_min = session.query(Measurement.date).first()
    date_range_min_str = str(date_range_min)
    date_range_min_str = re.sub("'|,", "",date_range_min_str)
    print (date_range_min_str)

    valid_entry_start = session.query(exists().where(Measurement.date == start)).scalar()
 	
    valid_entry_end = session.query(exists().where(Measurement.date == end)).scalar()

    if valid_entry_start and valid_entry_end:

    	results = (session.query(func.min(Measurement.tobs)
    				 ,func.avg(Measurement.tobs)
    				 ,func.max(Measurement.tobs))
    					  .filter(Measurement.date >= start)
    				  	  .filter(Measurement.date <= end).all())

    	tmin =results[0][0]
    	tavg ='{0:.4}'.format(results[0][1])
    	tmax =results[0][2]
    
    	result_printout =( ['Entered Start Date: ' + start,
    						'Entered End Date: ' + end,
    						'The lowest Temperature was: '  + str(tmin) + ' F',
    						'The average Temperature was: ' + str(tavg) + ' F',
    						'The highest Temperature was: ' + str(tmax) + ' F'])
    	return jsonify(result_printout)

    if not valid_entry_start and not valid_entry_end:
    	return jsonify({"error": f"Input Start {start} and End Date {end} not valid. Date Range is {date_range_min_str} to {date_range_max_str}"}), 404

    if not valid_entry_start:
    	return jsonify({"error": f"Input Start Date {start} not valid. Date Range is {date_range_min_str} to {date_range_max_str}"}), 404

    if not valid_entry_end:
    	return jsonify({"error": f"Input End Date {end} not valid. Date Range is {date_range_min_str} to {date_range_max_str}"}), 404  

if __name__ == "__main__":
    app.run(debug=True)