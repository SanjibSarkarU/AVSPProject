__author__ = 'Sanjib Sarkar'
__copyright__ = ''
__credits__ = ['', '']
__license__ = ''
__version__ = '1.0.0'
__date__ = '01/26/2022'
__maintainer__ = 'Sanjib Sarkar'
__email__ = 'sanjib.sarkar@usm.edu'
__status__ = 'Prototype'

import re


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


def received_stream(stream):
    if re.search("ACK", stream):
        acknowledgement = {'1': 'omstopACK', '8': 'osdAck', '11': 'opkAck', '16': 'omwAck'}
        rec_chksm = stream.split('*')[-1][0:3]
        cal_chksm = check_sum(stream.split(';')[-1][1:-2])
        if int(rec_chksm, 16) == int(cal_chksm, 16):
            stream =stream.split(';')[-1].split(',')
            ak = acknowledgement[stream[1]]
            if stream[2] == '0':
                print(f"{ak} received without an error")
                return 'ACK_WITHOUT_ERROR'
            else:
                print(f"{ak} received with the error code: {stream[3]}")
                return 'ACK_WITH_ERROR'
        else:
            print('wrong checksum')
            print('Received checkSum: ' + rec_chksm + 'Calculated checkSum: ' + cal_chksm)
    elif re.search("OSI", stream):
        return 'osi'
    elif re.search("OSD", stream):
        return 'osd'
    elif re.search("OMW", stream):
        return 'omw'
    elif stream == '':
        return 'None'
    else:
        return 'not known keyword'


def osi(stream):
    try:
        # print(stream)
        if int(stream.split('*')[-1], 16) == int(check_sum(stream.split(';')[-1][1:-2]), 16):
            # print('Right checkSum')
            stream = stream.split(',')
            mode = {'N': 'Normal_UVC', 'S': 'Stopped', 'P': 'Parking',
                    'M': 'Manual_Override', 'mP': 'Manual_parking',
                    'A': 'Servo', 'W': 'Waypoint'}
            # print('Mode : {}'.format(mode[stream[2]]))
            # print('NextWp: ', stream[3])
            # print('Latitude: ', stream[4])
            # print('Longitude: ', stream[5])
            # print('Speed: {} Knots'.format(stream[6]))
            # print("Distance to next WP: {} meters".format(stream[7]))
            # print('Battery percent: ', stream[16])
            # osi_return = (stream[3], stream[4], stream[5], stream[6], stream[7], stream[16])
            osi_return = {'Mode': mode[stream[2]], 'NextWp': stream[3], 'Latitude': float(stream[4]),
                          'Longitude': float(stream[5]), 'Speed': float(stream[6]), 'DistanceToNxtWP': float(stream[7]),
                          'Error': stream[8], 'Battery': float(stream[16]), 'SRP': stream[17]}
            return osi_return
        else:
            print('Wrong checkSum')
            print("Received checkSum: " + str(stream.split('*')[-1]) + 'Calculated checksum is : ' + str(
                check_sum(stream.split(';')[-1][1:-2])))
            print(" Wrong CheckSum: ", stream)
            # osi_return = {'NextWp': 0, 'Latitude': 00.00000, 'Longitude': 00.00000,
            #               'Speed': 0.00, 'DistanceToNxtWP': 0.00, 'Battery': 0.00}
            return None
    except Exception as osi_exception:
        print("Error: ", osi_exception)
        return None


def osd():
    ins_osd = 'OSD,,,S,,,,,*'
    instruction = ins_osd + check_sum(ins_osd)
    return instruction
