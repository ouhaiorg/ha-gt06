from homeassistant.const import STATE_HOME, STATE_NOT_HOME
import homeassistant.helpers.config_validation as cv

import datetime,time,socket,threading,json
import configparser,math,logging,sys,codecs
import voluptuous as vol

a = 6378245.0
ee = 0.00669342162296594323
x_pi = 3.14159265358979324 * 3000.0 / 180.0;
CRC_TAB = (
    0x0000, 0x1189, 0x2312, 0x329B, 0x4624, 0x57AD, 0x6536, 0x74BF,
    0x8C48, 0x9DC1, 0xAF5A, 0xBED3, 0xCA6C, 0xDBE5, 0xE97E, 0xF8F7,
    0x1081, 0x0108, 0x3393, 0x221A, 0x56A5, 0x472C, 0x75B7, 0x643E,
    0x9CC9, 0x8D40, 0xBFDB, 0xAE52, 0xDAED, 0xCB64, 0xF9FF, 0xE876,
    0x2102, 0x308B, 0x0210, 0x1399, 0x6726, 0x76AF, 0x4434, 0x55BD,
    0xAD4A, 0xBCC3, 0x8E58, 0x9FD1, 0xEB6E, 0xFAE7, 0xC87C, 0xD9F5,
    0x3183, 0x200A, 0x1291, 0x0318, 0x77A7, 0x662E, 0x54B5, 0x453C,
    0xBDCB, 0xAC42, 0x9ED9, 0x8F50, 0xFBEF, 0xEA66, 0xD8FD, 0xC974,
    0x4204, 0x538D, 0x6116, 0x709F, 0x0420, 0x15A9, 0x2732, 0x36BB,
    0xCE4C, 0xDFC5, 0xED5E, 0xFCD7, 0x8868, 0x99E1, 0xAB7A, 0xBAF3,
    0x5285, 0x430C, 0x7197, 0x601E, 0x14A1, 0x0528, 0x37B3, 0x263A,
    0xDECD, 0xCF44, 0xFDDF, 0xEC56, 0x98E9, 0x8960, 0xBBFB, 0xAA72,
    0x6306, 0x728F, 0x4014, 0x519D, 0x2522, 0x34AB, 0x0630, 0x17B9,
    0xEF4E, 0xFEC7, 0xCC5C, 0xDDD5, 0xA96A, 0xB8E3, 0x8A78, 0x9BF1,
    0x7387, 0x620E, 0x5095, 0x411C, 0x35A3, 0x242A, 0x16B1, 0x0738,
    0xFFCF, 0xEE46, 0xDCDD, 0xCD54, 0xB9EB, 0xA862, 0x9AF9, 0x8B70,
    0x8408, 0x9581, 0xA71A, 0xB693, 0xC22C, 0xD3A5, 0xE13E, 0xF0B7,
    0x0840, 0x19C9, 0x2B52, 0x3ADB, 0x4E64, 0x5FED, 0x6D76, 0x7CFF,
    0x9489, 0x8500, 0xB79B, 0xA612, 0xD2AD, 0xC324, 0xF1BF, 0xE036,
    0x18C1, 0x0948, 0x3BD3, 0x2A5A, 0x5EE5, 0x4F6C, 0x7DF7, 0x6C7E,
    0xA50A, 0xB483, 0x8618, 0x9791, 0xE32E, 0xF2A7, 0xC03C, 0xD1B5,
    0x2942, 0x38CB, 0x0A50, 0x1BD9, 0x6F66, 0x7EEF, 0x4C74, 0x5DFD,
    0xB58B, 0xA402, 0x9699, 0x8710, 0xF3AF, 0xE226, 0xD0BD, 0xC134,
    0x39C3, 0x284A, 0x1AD1, 0x0B58, 0x7FE7, 0x6E6E, 0x5CF5, 0x4D7C,
    0xC60C, 0xD785, 0xE51E, 0xF497, 0x8028, 0x91A1, 0xA33A, 0xB2B3,
    0x4A44, 0x5BCD, 0x6956, 0x78DF, 0x0C60, 0x1DE9, 0x2F72, 0x3EFB,
    0xD68D, 0xC704, 0xF59F, 0xE416, 0x90A9, 0x8120, 0xB3BB, 0xA232,
    0x5AC5, 0x4B4C, 0x79D7, 0x685E, 0x1CE1, 0x0D68, 0x3FF3, 0x2E7A,
    0xE70E, 0xF687, 0xC41C, 0xD595, 0xA12A, 0xB0A3, 0x8238, 0x93B1,
    0x6B46, 0x7ACF, 0x4854, 0x59DD, 0x2D62, 0x3CEB, 0x0E70, 0x1FF9,
    0xF78F, 0xE606, 0xD49D, 0xC514, 0xB1AB, 0xA022, 0x92B9, 0x8330,
    0x7BC7, 0x6A4E, 0x58D5, 0x495C, 0x3DE3, 0x2C6A, 0x1EF1, 0x0F78,
)

_LOGGER = logging.getLogger(__name__)

DEVICE_SCHEMA = vol.Schema(
    {
        vol.Optional("host", default="192.168.2.1"): cv.url,
        vol.Optional("port", default=5023): cv.positive_int
    }
)

class pipethread(threading.Thread):

    def __init__(self,source,hass,async_see):

        threading.Thread.__init__(self)
        self.source = source
        self.hass = hass
        self.async_see = async_see
        self.shost = None
        self.sport = None
        self.data = {"ACC": 0,"POWER": 0,"GPS": 0,"DEFENSE": 0,"powerLevel": 0,"gsmSignal": 0,"gpsRealtime": 0,"gpsPosition": 0,"latitude": 27.993384,"longitude": 120.700605,"speed": 0,"course": 0,"time": "2020-10-24 20:00:00"}                
        self.deviceID = "noname"
        self.longitude_home = hass.states.get('zone.home').attributes['longitude']
        self.latitude_home = hass.states.get('zone.home').attributes['latitude']
        self.radius_home = hass.states.get('zone.home').attributes['radius']/111000
        (self.shost,self.sport) = self.source.getpeername()
        _LOGGER.debug("new pipe create:(%s:%d)" % (self.shost,self.sport))
       
    def save_date(self):
        longitude = self.data['longitude']
        latitude = self.data['latitude']
        deviceID = self.deviceID
        if abs(latitude-self.latitude_home) < self.radius_home and abs(longitude-self.longitude_home) <  self.radius_home:
            location_name = STATE_HOME
        else :
            location_name = STATE_NOT_HOME
        see_args = {"dev_id": deviceID, "location_name": location_name}
        see_args["source_type"] = "gps"
        see_args["attributes"] = self.data 
        _LOGGER.debug("save data：%s" %self.data)
        self.hass.async_create_task(self.async_see(**see_args))    
          
    def run(self):

        last_data = b''
        while True:
            try:
                data=self.source.recv(1024)
                if not data: break
                if (data[0:2] != b'\x78\x78' and data[0:2] != b'\x79\x79'):
                    data = last_data + data
     
                if (data[0:2] != b'\x78\x78' and data[0:2] != b'\x79\x79'):
                   _LOGGER.debug("Data error.")
                   last_data=b''
                   continue     
                
                if(data[0:2]==b'\x78\x78'):
                    package_len_byte = 1
                    package_len = data[2] 
                else:
                    package_len_byte = 2
                    package_len = data[2]*256 + data[3]                
                if(len(data) < package_len + 4 + package_len_byte):
                    last_data = data
                    continue
                if(len(data) > package_len + 4 + package_len_byte):
                    last_data = data[package_len + 4 + package_len_byte:len(data)]
                    data = data[0:package_len + 4 + package_len_byte]
                else:
                    last_data = b''                
                _LOGGER.debug("[gt06<%s]%s"  %(self.shost,data.hex()))

                if (data[len(data)-2:len(data)]!=b'\x0D\x0A'):
                   _LOGGER.debug("Not End of 0D0A,Data error.")
                   continue

                gtp = data[2:len(data)-2]      
 
                if(crc16(gtp[0:len(gtp)-2]) != gtp[len(gtp)-2]*256 + gtp[len(gtp)-1] ):
                   _LOGGER.debug("Data crc error.")
                   continue
                serial_gtp = gtp[len(gtp)-4:len(gtp)-2]
                gtp = gtp[package_len_byte:len(gtp)-4]
                ptype = gtp[0]
#                _LOGGER.debug("Serial_gtp: %s"  %serial_gtp.hex())              
                if ptype == 0x01:
                   deviceID = gtp[1:9].hex()
                   if (deviceID[0] == '0'):
                       deviceID = deviceID[1:]
                   self.deviceID = deviceID    
                   rgtp = bytearray.fromhex("7878050100059FF80D0A")                  
                   rgtp[4:6] = serial_gtp
                   rgtp[6:8] = crc16(rgtp[2:6]).to_bytes(length=2,byteorder='big')
                   _LOGGER.debug("[gt06>%s]%s" %(self.shost,rgtp.hex()))
                   self.source.send(rgtp)
                elif ptype == 0x13:
                   self.data["powerLevel"] = gtp[2]
                   self.data["gsmSignal"] = gtp[3]
                   self.data["GPS"] = 1 if gtp[1]&0x40 else 0
                   self.data["POWER"] = 1 if gtp[1]&0x04 else 0
                   self.data["ACC"] = 1 if gtp[1]&0x02 else 0
                   self.data["DEFENSE"] = 1 if gtp[1]&0x01 else 0
                   self.save_date()
                   rgtp = bytearray.fromhex("78780513000f008F0D0A")     
                   rgtp[4:6] = serial_gtp
                   rgtp[6:8] = crc16(rgtp[2:6]).to_bytes(length=2,byteorder='big')
                   _LOGGER.debug("[gt06>%s]%s" %(self.shost,rgtp.hex()))
                   self.source.send(rgtp)
                elif ptype == 0x22:
                   latitude = (gtp[8]*256*256*256 + gtp[9]*256*256 +gtp[10]*256 + gtp[11]) / 1800000.0
                   longitude = (gtp[12]*256*256*256 + gtp[13]*256*256 +gtp[14]*256 + gtp[15]) / 1800000.0
                   self.data["speed"] = gtp[16]
                   self.data["course"] = (gtp[17]&0x03)*256 + gtp[18]
                   cst_time = datetime.datetime(2000+gtp[1],gtp[2],gtp[3],gtp[4],gtp[5],gtp[6]) + datetime.timedelta(hours=8) 
                   self.data["time"] = cst_time.strftime("%Y-%m-%d %H:%M:%S")
                   
                   self.data["gpsRealtime"] = 0 if gtp[17]&0x20 else 1
                   self.data["gpsPosition"] = 1 if gtp[17]&0x10 else 0
                   EastLongitude = False if gtp[17]&0x08 else True
                   NorthLatitude = True if gtp[17]&0x04 else False
                   if EastLongitude and NorthLatitude :
                       (latitude,longitude) = wgs2gcj(latitude, longitude)
                   else:
                       latitude = latitude if NorthLatitude else -latitude
                       longitude = longitude if EastLongitude else -longitude
                   self.data["latitude"] = round(latitude, 6)
                   self.data["longitude"] = round(longitude, 6)                       
                   self.save_date()
                   rgtp = bytearray.fromhex("7878052201a6fdee0d0a")
                   rgtp[4:6] = serial_gtp
                   rgtp[6:8] = crc16(rgtp[2:6]).to_bytes(length=2,byteorder='big')
                   _LOGGER.debug("[gt06>%s]%s" %(self.shost,rgtp.hex()))
                   self.source.send(rgtp)
                elif ptype == 0x80:
                   _LOGGER.debug("ptype====%X" %ptype)  
                elif ptype == 0x97:
                   _LOGGER.debug("ptype====%X" %ptype)
                elif ptype == 0x8a:
                   rgtp = bytearray.fromhex("78780B8A0F0C1D0000150006F0860D0A")
                   rgtp[10:12] = serial_gtp
                   now = datetime.datetime.now()
                   rgtp[4] = now.year - 2000
                   rgtp[5] = now.month
                   rgtp[6] = now.day
                   rgtp[7] = now.hour
                   rgtp[8] = now.minute
                   rgtp[9] = now.second
                   _LOGGER.debug("[gt06>%s]%s" %(self.shost,rgtp.hex()))
                   rgtp[12:14] = crc16(rgtp[2:12]).to_bytes(length=2,byteorder='big')
                   self.source.send(rgtp)
                elif ptype == 0x94:
                   itype = gtp[1]
                   if itype == 0x0a:
                       IMEI = gtp[2:10].hex()
                       IMSI = gtp[10:18].hex()
                       ICCID = gtp[18:28].hex()
                       _LOGGER.debug("info:" + self.deviceID + ";IMEI:" + IMEI + ";IMSI:" + IMSI + ";ICCID:" + ICCID)
                   elif itype == 0x04:
                        _LOGGER.debug("info:" + self.deviceID + ":" + gtp[2:].decode('utf-8'))        
                   elif itype == 0x09:   
                       _LOGGER.debug("info:" + self.deviceID + ":" + gtp[2:].hex())        
                   else:                    
                       _LOGGER.debug("info:" + self.deviceID + ":" + gtp[2:].hex())                                
                elif ptype == 0x21:
                  _LOGGER.debug("info:" + self.deviceID + ":" + gtp[6:].decode('utf-8'))
                else:
                   _LOGGER.debug("ptype====%X" %ptype)                
            except Exception as ex:
                _LOGGER.debug("redirect error:"+str(ex))

def transformLat(lat,lon):
    ret = -100.0 + 2.0 * lat + 3.0 * lon + 0.2 * lon * lon + 0.1 * lat * lon +0.2 * math.sqrt(abs(lat))
    ret += (20.0 * math.sin(6.0 * lat * math.pi) + 20.0 * math.sin(2.0 * lat * math.pi)) * 2.0 / 3.0
    ret += (20.0 * math.sin(lon * math.pi) + 40.0 * math.sin(lon / 3.0 * math.pi)) * 2.0 / 3.0
    ret += (160.0 * math.sin(lon / 12.0 * math.pi) + 320 * math.sin(lon * math.pi  / 30.0)) * 2.0 / 3.0
    return ret

def transformLon(lat,lon):
    ret = 300.0 + lat + 2.0 * lon + 0.1 * lat * lat + 0.1 * lat * lon + 0.1 * math.sqrt(abs(lat))
    ret += (20.0 * math.sin(6.0 * lat * math.pi) + 20.0 * math.sin(2.0 * lat * math.pi)) * 2.0 / 3.0
    ret += (20.0 * math.sin(lat * math.pi) + 40.0 * math.sin(lat / 3.0 * math.pi)) * 2.0 / 3.0
    ret += (150.0 * math.sin(lat / 12.0 * math.pi) + 300.0 * math.sin(lat / 30.0 * math.pi)) * 2.0 / 3.0
    return ret
    
def wgs2gcj(lat,lon):
    dLat = transformLat(lon - 105.0, lat - 35.0)
    dLon = transformLon(lon - 105.0, lat - 35.0)
    radLat = lat / 180.0 * math.pi
    magic = math.sin(radLat)
    magic = 1 - ee * magic * magic
    sqrtMagic = math.sqrt(magic)
    dLat = (dLat * 180.0) / ((a * (1 - ee)) / (magic * sqrtMagic) * math.pi)
    dLon = (dLon * 180.0) / (a / sqrtMagic * math.cos(radLat) * math.pi)
    mgLat = lat + dLat
    mgLon = lon + dLon
    loc=[mgLat,mgLon]
    return loc

def crc16(data):
    crc_tab = CRC_TAB  # minor optimization: put CRC_TAB to locals()
    fcs = 0xffff
    for b in iter(data):
        index = (fcs ^ b) & 0xff
        fcs = (fcs >> 8) ^ crc_tab[index]
    return fcs ^ 0xffff


class s2mqtt(threading.Thread):
    def __init__(self,host,port,hass,async_see):
        threading.Thread.__init__(self)
        self.hass=hass
        self.async_see=async_see
        self.sock=None
        self.sock=socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        self.sock.bind((host,port))
        self.sock.setsockopt(socket.SOL_TCP, socket.TCP_NODELAY, 1)
        self.sock.listen(5)
        _LOGGER.debug("start listen on [%s:%d]." % (host,port))
    def run(self):
        while True:
            newsock,address=self.sock.accept()
            _LOGGER.debug("new connect from [%s:%s]." %(address[0],address[1]))
            p1=pipethread(newsock,self.hass,self.async_see)
            p1.start()

async def async_setup_scanner(hass, config, async_see, discovery_info=None):

    host = config["host"]
    port = config["port"]
    mapp = s2mqtt(host,port,hass,async_see)
    mapp.start()   
    return True

