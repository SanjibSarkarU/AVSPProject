class IverRequestDecode:
    """ WORK IN PROGRESS.......Iver Simulation supporting file.
    Decode a request(like OSD, STOP, OMW etc.),
        Check Checksum of the incoming stream and return the information.
        input : '$AC;Iver3-3089;$OMW,CLEAR,30.35197,-89.62897,0.0,,10,4.0,0, *cc'
                                $OMW,<LAT>,<LNG>,<Depth1>,<Depth2>,<Max Angle><SPD>,<Park>,<Sensors><*cc>
                                'OSD,,,S,,,,,*'
                                $OSD,<GPS>,<COMPASS>,<STATE>,<POWER>,<YSI>,<DVL>,<CTD>,<INS><*cc>
                                'OMSTOP,0*'
                                $OMSTOP,<FL><*cc>
        return: {key, info} """

    def __init__(self):
        self.info = None
        self.stream = None

    def extract_info(self, stream):
        self.stream = stream
        if not stream.endswith('\r\n'):
            logger.debug('Time out.')
            return None
        if not stream.startswith('$AC'):
            logger.debug('$AC is missing')
            return None
        if not re.search('\*', stream):
            logger.debug('* is missing')
            return None
        stream = stream.rstrip('\r\n')
        ac, iver_sign, message_with_cs = stream.split(';')
        message, cs = message_with_cs.split('*')
        if not len(cs) == 2:
            logger.debug(f'Wrong checkSum format:{cs}')
            return None
        if int(cs, 16) != int(check_sum(message), 16):
            logger.debug(f'Wrong CheckSum:{cs}')
            return None
        message = message.lstrip('$')
        if re.search('OSD', message):
            info = osd_request_decode(message)
            return {'Key': 'OSD', 'Info': info}
        elif re.search('OMSTOP', message):
            return {'Key': 'OMSTOP', 'Info': 0 if message == '$OMSTOP,0' else None}
        elif re.search('OMW', message):
            """OMW,CLEAR,30.35197,-89.62897,0.0,,10,4.0,0,
                 OMW,<!CLEAR!>,<LAT>,<LNG>,<Depth1>,<Depth2>,<Max Angle><SPD>,<Park>,<Sensors>"""
            key = 'OMWC' if re.search('CLEAR', message) else 'OMW'
            message = stream.split(',')[1:]
            return {'Key': key, 'Info': {'lat': message[1], 'lng': message[2], 'speed': message[6]}}


stream = '$AC;Iver3-3089;$OMSTOP,0*06'