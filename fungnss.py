__author__ = 'Sanjib Sarkar'
__copyright__ = ''
__credits__ = ['', '']
__license__ = ''
__version__ = '1.0.0'
__date__ = '01/06/2022'
__maintainer__ = 'Sanjib Sarkar'
__email__ = 'sanjib.sarkar@usm.edu'
__status__ = 'Prototype'

import re

from geographiclib.geodesic import Geodesic


def check_sum(instruction):
    """ Remove any newlines and $ and calculate checksum """
    if re.search("\n$", instruction):
        instruction = instruction[:-1]
    if re.search("\r$", instruction):
        instruction = instruction[:-1]
    if re.search("\$", instruction):
        instruction = instruction[1:]
    nmeadata, cksum = re.split('\*', instruction)
    calc_cksum = 0
    for s in nmeadata:
        calc_cksum ^= ord(s)
    """ Return the calculated checksum """
    return '{:02X}'.format(calc_cksum)


# ddm = degree, decimal minutes, dd = degree decimal
def ddm2dd(coordinates) -> dict:
    """ Convert degree, decimal minutes to degree decimal; return {'Lat_dd': float, 'Lng_dd': float}
    Input Ex.:  ['3020.1186383580', 'N', '0894.5222887340', 'W'],
    return: {'Lat_dd': float(lat_dd), 'Lng_dd': float(lng_dd)} """
    lat, lat_direction, lng, lng_direction = coordinates[0], coordinates[1], coordinates[2], coordinates[3]
    lat = lat[1:] if lat.startswith('0') else lat
    lat_ddm = lat[:2] + str(float(lat[2:]) / 60)[1:]
    lat_dd = '{}'.format(lat_ddm if lat_direction == 'N' else '-' + lat_ddm)
    lng = str(int(lng[:3])) + str(float(lng[3:]) / 60)[1:]
    lng_dd = '{}'.format(lng if lng_direction == 'E' else '-' + lng)
    dd = {'Lat_dd': float(lat_dd), 'Lng_dd': float(lng_dd)}
    return dd


def gpglldecode(gpgllstr: str) -> dict:
    """"Takes GPGLL string and returns degree decimal
    input: '$GPGLL,3021.0378,N,08937.806599999999996,W,104129,A,A*6E'
    return: {'Lat_dd': float, 'Lng_dd': float}"""
    if int((gpgllstr.split('*')[-1]), 16) == int(check_sum(gpgllstr.split('*')[0] + '*'), 16):
        key_word, lat, lat_direction, lng, lng_direction, t, status, mode = gpgllstr.split(',')
        if key_word == '$GPGLL':
            if status == 'A':
                lat_dd = float(lat[:2]) + float(lat[2:]) / 60
                lat_dd = lat_dd if lat_direction == 'N' else -1 * lat_dd
                lng = str(int(lng[:3])) + str(float(lng[3:]) / 60)[1:]
                lng_dd = '{}'.format(lng if lng_direction == 'E' else '-' + lng)
                dd = {'Lat_dd': float(lat_dd), 'Lng_dd': float(lng_dd), 'time': t}
                return dd
            else:
                print('fungnss>gpglldecode> The status is not VALID')
        else:
            print('fungnss>gpglldecode> this is not a GPGLL string')
    else:
        print("fungnss>gpglldecode>Wrong CheckSum: received checkSum{}, calculated checkSum{}".format(
            gpgllstr.split('*')[-1], check_sum(gpgllstr.split('*')[0] + '*')))


def dd2ddm(coordinates):
    """ Convert degree decimal to degree decimal minute;
     return: {'Lat_ddm': lat_ddm, 'N_S': 'S' if lat_sign else 'N',
           'Lng_ddm': lng_ddm, 'E_W': 'W' if lng_sign else 'E'}"""
    lat, lng = str(coordinates[0]), str(coordinates[1])
    lat_sign = lat.startswith('-')
    lat = '{}'.format(lat[1:] if lat.startswith('-') else lat)
    lat_ddm = lat[:2] + str(float(lat[2:]) * 60)
    lng_sign = lng.startswith('-')
    lng = '{}'.format(lng[1:] if lng.startswith('-') else lng)
    lng_ddm = lng[:2] + str(float(lng[2:]) * 60)
    lng_ddm = lng_ddm.zfill(len(lng_ddm) + 1)
    ddm = {'Lat_ddm': lat_ddm, 'N_S': 'S' if lat_sign else 'N',
           'Lng_ddm': lng_ddm, 'E_W': 'W' if lng_sign else 'E'}
    return ddm


def speed_heading_cal(coor1_withtime, coor2_withtime) -> dict:
    """ Return heading angle, speed, and distance;
    input:coordinates with timestamp: ['30.35059', '-89.62995', '104139'],
                                      ['30.35059', '-89.62995', '104139'] """

    geod = Geodesic(6378388, 1 / 297.0)
    lat_co1, lng_co1, t_co1 = coor1_withtime[0], coor1_withtime[1], str(coor1_withtime[-1])
    lat_co2, lng_co2, t_co2 = coor2_withtime[0], coor2_withtime[1], str(coor2_withtime[-1])
    d = geod.Inverse(float(lat_co1), float(lng_co1), float(lat_co2), float(lng_co2))
    distance = d['s12']
    ha = d['azi2']
    time_diff = (int(t_co2[0:2]) * 3600 + int(t_co2[2:4]) * 60 + float(t_co2[4:])) - \
                (int(t_co1[0:2]) * 3600 + int(t_co1[2:4]) * 60 + float(t_co1[4:]))
    try:
        speed = distance / time_diff
        result = {'speed': speed, 'ha': ha, 'dis12': distance}
    except ZeroDivisionError:
        print('Time difference between two coordinates is zero.')
        result = None
    return result
