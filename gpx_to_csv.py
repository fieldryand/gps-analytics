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
              'speed',
              'dist_from_start']

    with open(filename, 'w') as file:
        writer = csv.writer(file)
        writer.writerow(fields)
        points_data = x.get_points_data()
        for t, track in enumerate(x.tracks):
            track_points_data = [p for p in points_data if p.track_no == t]
            moving_data = track.get_moving_data()
            time_bounds = track.get_time_bounds()
            bounds = track.get_bounds()
            for k, segment in enumerate(track.segments):
                segment_points_data = [p for p in track_points_data if p.segment_no == k]
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
                                     speed_kmh,
                                     segment_points_data[i].distance_from_start
                                     ))


def drop_extension(filename: str) -> str:
    """Drop the extension from a filename"""
    return filename.split('.')[0]


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
