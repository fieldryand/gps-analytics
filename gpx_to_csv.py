"""
Transform GPX files to CSV
"""

import csv

import gpxpy


def ms_to_kmh(speed: float) -> float:
    """Convert speed in m/s to km/h"""
    return speed * 60 * 60 / 1000


def to_csv(x: gpxpy.gpx.GPX, filename: str):
    """Write parts of a GPX object to CSV"""
    fields = ['gpx_name',
              'trk_name',
              'trk_mov_time',
              'trk_mov_dist',
              'trk_start_time',
              'trk_end_time',
              'trk_max_lat',
              'trk_max_long',
              'trk_min_lat',
              'trk_min_long',
              'segment_num',
              'lat',
              'long',
              'ele',
              'time',
              'speed']

    with open(filename, 'w') as file:
        writer = csv.writer(file)
        writer.writerow(fields)
        for track in x.tracks:
            moving_data = track.get_moving_data()
            time_bounds = track.get_time_bounds()
            bounds = track.get_bounds()
            for k, segment in enumerate(track.segments):
                for i, point in enumerate(segment.points):
                    speed_kmh = ms_to_kmh(segment.get_speed(i))
                    writer.writerow((x.name,
                                     track.name,
                                     moving_data.moving_time,
                                     moving_data.moving_distance,
                                     time_bounds.start_time,
                                     time_bounds.end_time,
                                     bounds.max_latitude,
                                     bounds.max_longitude,
                                     bounds.min_latitude,
                                     bounds.min_longitude,
                                     k,
                                     point.latitude,
                                     point.longitude,
                                     point.elevation,
                                     point.time,
                                     speed_kmh))


def drop_extension(filename: str) -> str:
    """Drop the extension from a filename"""
    return filename.split('.')[0]


# Monkey patch pre-release bug fixes
from typing import Optional, cast
import datetime as mod_datetime

import gpxpy.utils as mod_utils
import gpxpy.geo as mod_geo
from gpxpy.gpx import MovingData

DEFAULT_STOPPED_SPEED_THRESHOLD = 1


def total_seconds(timedelta: mod_datetime.timedelta) -> float:
    """ Some versions of python don't have the timedelta.total_seconds() method. """
    if timedelta is None:
        return None
    return_seconds = cast(float, (timedelta.days * 86400) + timedelta.seconds)
    if timedelta.microseconds > 0:
        return_seconds += timedelta.microseconds/1000000.0
    return return_seconds


gpxpy.utils.total_seconds = total_seconds


def get_moving_data(self, stopped_speed_threshold: Optional[float]=None) -> Optional[MovingData]:
    """
    Return a tuple of (moving_time, stopped_time, moving_distance,
    stopped_distance, max_speed) that may be used for detecting the time
    stopped, and max speed. Not that those values are not absolutely true,
    because the "stopped" or "moving" information aren't saved in the segment.
    Because of errors in the GPS recording, it may be good to calculate
    them on a reduced and smoothed version of the track.
    Parameters
    ----------
    stopped_speed_threshold : float
        speeds (km/h) below this threshold are treated as if having no
        movement. Default is 1 km/h.
    Returns
    ----------
    moving_data : MovingData : named tuple
        moving_time : float
            time (seconds) of segment in which movement was occurring
        stopped_time : float
            time (seconds) of segment in which no movement was occurring
        stopped_distance : float
            distance (meters) travelled during stopped times
        moving_distance : float
            distance (meters) travelled during moving times
        max_speed : float
            Maximum speed (m/s) during the segment.
    """
    if not stopped_speed_threshold:
        stopped_speed_threshold = DEFAULT_STOPPED_SPEED_THRESHOLD

    moving_time = 0.
    stopped_time = 0.

    moving_distance = 0.
    stopped_distance = 0.

    speeds_and_distances = []

    for i in range(1, len(self.points)):

        previous = self.points[i - 1]
        point = self.points[i]

        # Won't compute max_speed for first and last because of common GPS
        # recording errors, and because smoothing don't work well for those
        # points:
        if point.time and previous.time:
            timedelta = point.time - previous.time

            if point.elevation and previous.elevation:
                distance = point.distance_3d(previous)
            else:
                distance = point.distance_2d(previous)

            seconds = mod_utils.total_seconds(timedelta)
            speed_kmh: float = 0
            if seconds > 0 and distance is not None:
                # TODO: compute threshold in m/s instead this to kmh every time:
                speed_kmh = (distance / 1000.) / (seconds / 60. ** 2)
                if distance:
                    if speed_kmh <= stopped_speed_threshold:
                        stopped_time += seconds
                        stopped_distance += distance
                    else:
                        moving_time += seconds
                        moving_distance += distance
                    if moving_time:
                        speeds_and_distances.append((distance / seconds, distance, ))

    max_speed = None
    if speeds_and_distances:
        max_speed = mod_geo.calculate_max_speed(speeds_and_distances)

    return MovingData(moving_time, stopped_time, moving_distance, stopped_distance, max_speed or 0.0)


gpxpy.gpx.GPXTrackSegment.get_moving_data = get_moving_data
# End monkey patch


if __name__ == '__main__':
    import os
    import argparse

    parser = argparse.ArgumentParser(description='Transform GPX files to CSV.')
    parser.add_argument('-i', '--input', help='the directory containing GPX files')
    parser.add_argument('-o', '--output', help='the directory in which to write the output')

    args = parser.parse_args()

    assert os.path.isdir(args.input)
    assert os.path.isdir(args.output)

    for f in os.listdir(args.input):
        gpx_file = open(os.path.join(args.input, f), 'r')
        gpx = gpxpy.parse(gpx_file)
        target_file = os.path.join(args.output, drop_extension(f) + '.csv')
        to_csv(gpx, target_file)
        print('Wrote to {}'.format(target_file))

    print('Done.')
