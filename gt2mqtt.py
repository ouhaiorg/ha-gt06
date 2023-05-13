#-* -coding: UTF-8 -* -
import datetime,time,socket,threading,json
import paho.mqtt.client as mqtt
import requests,configparser,math,copy
import os,sys,logging,logging.handlers

a = 6378245.0
ee = 0.00669342162296594323
x_pi = 3.14159265358979324 * 3000.0 / 180.0;

f_dir = os.path.abspath((os.path.dirname(__file__)))
f_name = sys.argv[0].split('/')[-1].split('.')[0]

rfh = logging.handlers.RotatingFileHandler(
    filename = '/var/log/' + f_name + '.log',
    mode = 'a',
    maxBytes = 10 * 1024 * 1024,
    backupCount = 2,
    encoding = None,
    delay = 0
)

logging.basicConfig(
    level = logging.DEBUG,
    handlers = [rfh],
    datefmt = "%y-%m-%d %H:%M:%S",
    format = "%(asctime)s - %(levelname)s: %(message)s"
)

def log(strLog):
    logger = logging.getLogger('main')
    logger.info(strLog)

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
    
class pipethread2(threading.Thread):
    def __init__(self,pipe1):
        threading.Thread.__init__(self)
        self.pipe = pipe1
        self._stop_event = threading.Event()
    
    def stop(self):
        log("Threading Stop")
    
    def close(self):
       return self._stop_event.set()

    def stopped(self):
       return self._stop_event.is_set()

    def run(self):
        while not self.stopped():
            time.sleep(90)
            time2 = int(time.time()) - self.pipe.time
            log("Threading HeartBeat......" + str(time2) + "s")
            #if (time2 > 545):
           #     self.pipe.Flag = False
           #      self.pipe.mqtt.send(self.pipe.deviceID + '/state', 'offline')
            if (time2 > 185 and time2 < 545):
                if self.pipe.data["ACC"]:
                   self.pipe.set_accoff()
                   log("timeout:" + str(time2) + "s, call accOff_function")
                   self.pipe.accOff_func()
                   self.pipe.mqtt.send(self.pipe.deviceID + '/attributes', json.dumps(self.pipe.data))
            elif (time2 > 900):
                   log("timeout >900s;close threading")
                   self.pipe.close()
                   self.pipe.mqtt.client.disconnect()
                   self.pipe.source.shutdown(socket.SHUT_RDWR)
                   self.pipe.source.close()
                   self.close()
                  

class pipethread(threading.Thread):
    '''
    classdocs
    '''
    def __init__(self,source,mqtt,pos_home):
        '''
        Constructor
        '''
        threading.Thread.__init__(self)
        self.source=source
        self.shost = None
        self.sport = None
        self.mqtt = mqtt
        self.Flag = True
        self.time = int(time.time())
        self.data = {"ACC": 0,"POWER": 0,"GPS": 0,"DEFENSE": 0,"powerLevel": 0,"gsmSignal": 0,"gpsRealtime": 0,"gpsPosition": 0,"latitude": 27.973684,"longitude": 120.709219,"speed": 0,"course": 0,"time": "2023-04-23 08:12:36","position": "香缇车库", "distance": 0,"duration": 0,"home":"home"}

        self.pos_home = pos_home
        self.radius_home = 100/111000
        self.deviceID = "noname"
        self.amap_key = ""  #from lbs.amap.com get web service key
        self.baidu_key = ""  #from lbsyun.baidu.com get AK
        (self.shost,self.sport) = self.source.getpeername()
        self._stop_event = threading.Event()
        log("New Pipe create:(%s:%d)" % (self.shost,self.sport))
          
    def close(self):
       return self._stop_event.set()

    def stopped(self):
       return self._stop_event.is_set()

    def run(self):

        last_data = b''
        p2=pipethread2(self)
        p2.start()
        while not self.stopped():
            try:
                data=self.source.recv(1024)
                if not data: break
                if (data[0:2] != b'\x78\x78' and data[0:2] != b'\x79\x79'):
                    data = last_data + data
     
                if (data[0:2] != b'\x78\x78' and data[0:2] != b'\x79\x79'):
                   log("Data error.")
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
                log("[gt06<%s]%s"  %(self.shost,data.hex()))

                if (data[len(data)-2:len(data)]!=b'\x0D\x0A'):
                   log("Not End of 0D0A,Data error.")
                   continue

                gtp = data[2:len(data)-2]      
 
                if(crc16(gtp[0:len(gtp)-2]) != gtp[len(gtp)-2]*256 + gtp[len(gtp)-1] ):
                   log("Data crc error.")
                   continue
                serial_gtp = gtp[len(gtp)-4:len(gtp)-2]
                gtp = gtp[package_len_byte:len(gtp)-4]
                ptype = gtp[0]
#                log("Serial_gtp: %s"  %serial_gtp.hex())              
                if ptype == 0x01:
                   self.deviceID = gtp[1:9].hex()
                   if (self.deviceID[0] == '0'):
                       self.deviceID = self.deviceID[1:]
                   send_data = { "IMEI": self.deviceID }
                   self.mqtt.setDeviceID(self.deviceID)                   
                   self.mqtt.send("gt2mqtt/info/" + self.deviceID, json.dumps(send_data))
                   rgtp = bytearray.fromhex("7878050100059FF80D0A")
                   
                   rgtp[4:6] = serial_gtp
                   rgtp[6:8] = crc16(rgtp[2:6]).to_bytes(length=2,byteorder='big')
                   log("[gt06>%s]%s" %(self.shost,rgtp.hex()))
                   self.source.send(rgtp)
                   self.update_data(self.deviceID)
                elif ptype == 0x13:
                   self.data["powerLevel"] = gtp[2]
                   self.data["gsmSignal"] = gtp[3]
                   self.data["GPS"] = 1 if gtp[1]&0x40 else 0
                   self.data["POWER"] = 1 if gtp[1]&0x04 else 0
                   if (gtp[1]&0x02 == 0) and self.data["ACC"] : 
                      log("acc turn off, call accOff_function")
                      self.accOff_func()
                   self.data["ACC"] = 1 if gtp[1]&0x02 else 0
                   self.data["DEFENSE"] = 1 if gtp[1]&0x01 else 0
                   self.time = int(time.time())
                   self.mqtt.send(self.deviceID + '/attributes', json.dumps(self.data))
                   rgtp = bytearray.fromhex("78780513000f008F0D0A")     
                   rgtp[4:6] = serial_gtp
                   rgtp[6:8] = crc16(rgtp[2:6]).to_bytes(length=2,byteorder='big')
                   log("[gt06>%s]%s" %(self.shost,rgtp.hex()))
                   self.source.send(rgtp)
                elif ptype == 0x22:
                   latitude = (gtp[8]*256*256*256 + gtp[9]*256*256 +gtp[10]*256 + gtp[11]) / 1800000.0
                   longitude = (gtp[12]*256*256*256 + gtp[13]*256*256 +gtp[14]*256 + gtp[15]) / 1800000.0#
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
                   if abs(latitude - self.pos_home['latitude']) < self.radius_home and abs(longitude - self.pos_home['longitude']) <  self.radius_home:
                      location_home = 'home' 
                   else:
                      location_home = 'not_home'
                   if  location_home != self.data["home"] :
                      self.mqtt.send(self.deviceID + '/state', location_home)
                      self.data["home"] = location_home
                      log("home change to %s " %location_home)
                   self.time = int(time.time())
                   self.mqtt.send(self.deviceID + '/attributes', json.dumps(self.data))                 
                   rgtp = bytearray.fromhex("7878052201a6fdee0d0a")
                   rgtp[4:6] = serial_gtp
                   rgtp[6:8] = crc16(rgtp[2:6]).to_bytes(length=2,byteorder='big')
                   log("[gt06>%s]%s" %(self.shost,rgtp.hex()))
                   self.source.send(rgtp)
                elif ptype == 0x80:
                   log("ptype====%X" %ptype)  
                elif ptype == 0x97:
                   log("ptype====%X" %ptype)
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
                   log("[gt06>%s]%s" %(self.shost,rgtp.hex()))
                   rgtp[12:14] = crc16(rgtp[2:12]).to_bytes(length=2,byteorder='big')
                   self.source.send(rgtp)
                elif ptype == 0x94:
                   itype = gtp[1]
                   if itype == 0x0a:
                       IMEI = gtp[2:10].hex()
                       IMSI = gtp[10:18].hex()
                       ICCID = gtp[18:28].hex()
                       self.mqtt.send("gt2mqtt/info/" + self.deviceID, "IMEI:" + IMEI + ";IMSI:" + IMSI + ";ICCID:" + ICCID)
                   elif itype == 0x04:
                       self.mqtt.send("gt2mqtt/info/" + self.deviceID, gtp[2:].decode('utf-8'))        
                   elif itype == 0x09:   
                       self.mqtt.send("gt2mqtt/info/" + self.deviceID, gtp[2:].hex())        
                   else:                    
                       self.mqtt.send("gt2mqtt/info/" + self.deviceID, gtp[2:].hex())                                
                elif ptype == 0x21:
                   self.mqtt.send("gt2mqtt/info/" + self.deviceID, gtp[6:].decode('utf-8'))
                else:
                   log("ptype====%X" %ptype)                
            except Exception as ex:
                log("redirect error:"+str(ex))

    def set_pos(self,str,dist,dura):
      self.data['position'] = str
      self.data['distance'] = dist 
      self.data['duration'] = dura 
 
    def update_data(self, deviceID):
        data_file = f_dir + "/" + f_name + ".ini"
        if not os.path.isfile(data_file):
           log("Error: %s does not exist!" % data_file)
           return
        cf=configparser.ConfigParser("")
        cf.read(data_file)
        self.data["latitude"]=cf.getfloat(deviceID,"latitude")
        if cf.has_section(deviceID):
          self.data["longitude"]=cf.getfloat(deviceID,"longitude")
          self.data["time"]=cf.get(deviceID,"time")
          self.data["position"]=cf.get(deviceID,"position")
          self.data["distance"]=cf.getint(deviceID,"distance")
          self.data["duration"]=cf.getint(deviceID,"duration")
          self.data["home"]=cf.get(deviceID,"home")
    
    def save_data(self):
        data_file = f_dir + "/" + f_name + ".ini"
        cf=configparser.ConfigParser("")
        try:
           cf.read(data_file)
           if not cf.has_section(self.deviceID):
              cf.add_section(self.deviceID)
           cf.set(self.deviceID,"latitude",str(self.data["latitude"]))
           cf.set(self.deviceID,"longitude",str(self.data["longitude"]))
           cf.set(self.deviceID,"position",self.data["position"])
           cf.set(self.deviceID,"distance",str(self.data["distance"]))
           cf.set(self.deviceID,"duration",str(self.data["duration"]))
           cf.set(self.deviceID,"time",self.data["time"])
           cf.set(self.deviceID,"home",self.data["home"])
           cf.write(open(data_file,'w'))
           log("save data to file:%s" %data_file)
        except Exception as e:
           log("save data to %s error:" %(data_file,e.args))
           return None

    def set_accoff(self):
       self.data["ACC"] = 0
       self.data["speed"] = 0
       self.data["gsmSignal"] = 0
       self.data["gsmSignal"] = 0

    def accOff_func(self):
      if self.baidu_key =="" or self.amap_key == "":
          return
      cur_pos = "unknown"
      dist = 0
      dura = 0
      longitude_str = str(self.data['longitude'])
      latitude_str = str(self.data['latitude'])
      url = "https://restapi.amap.com/v3/geocode/regeo?output=json&location="+longitude_str+","+latitude_str+"&key="+self.amap_key+"&radius=1000&extensions=all"
      res = requests.get(url)
      if res.status_code == 200:
         cur_pos = res.json()["regeocode"]["formatted_address"]
      log("Get current postion:%s" %cur_pos)
      if self.data['home'] != 'home':
         url = "http://api.map.baidu.com/routematrix/v2/driving?output=json&origins=" + latitude_str + "," + longitude_str + "&destinations=" + str(self.pos_home['latitude']) + "," + str(self.pos_home['longitude']) + "&coord_type=gcj02&tactics=12&ak="+self.baidu_key
         res = requests.get(url)
         if res.status_code == 200:
            dist = res.json()["result"][0]["distance"]["value"]
            dura = res.json()["result"][0]["duration"]["value"]
         log("Get current distance:%d;duration:%d" %(dist,dura))
      self.set_pos(cur_pos, dist, dura)
      self.save_data()

class mqtt2(threading.Thread):
    def __init__(self,host,port,sock,muser,mpassword):
        threading.Thread.__init__(self)
        self.host = host 
        self.port = port
        self.sock = sock
        self.serial = b'\x00\x00'
        self.client = mqtt.Client()
        self.deviceID = "noname"
        self.client.username_pw_set(muser,mpassword)
        
        self.client.on_message = self.on_message_come # 消息到来处理函数
        self.client.on_connect = self.on_connect
  #      log("New Pipe create:%s->%s" % (self.sock.getpeername()))
   
    def run(self):
        self.client.connect(self.host, self.port,60)
        self.client.loop_forever()
    
    def on_connect(self, client, userdata, flags, rc):
        self.client.subscribe("gt2mqtt/command/#", 1)
        log("conncet MQTT [%s:%d] with code:%s." %(self.host,self.port,str(rc)))
         
    def send(self, topic, data):
        self.client.publish(topic, data, 0)
        log("Send MQTT:%s." %data)
    def setDeviceID(self,deviceID):
        self.deviceID = deviceID    
           
    def on_message_come(self, client, userdata, msg):
        log("MQTT Received,Topic:"+ msg.topic + ";Payload:"+ msg.payload.decode('utf-8'))
        if self.sock:
            try:
                topic = msg.topic
                payload = msg.payload
                length = len(msg.payload)
                if( msg.topic == "gt2mqtt/command/" + self.deviceID and length >= 4):
                   if(payload[0]== ord('[') and payload[length-1]== ord(']')): 
                       data = payload[1:length-1]
                       if data[len(data)-1] == ord('#'):
                          rgtp = bytearray.fromhex("787810800a00000000")
                          rgtp[4]=len(data)+4
                          rgtp[2]=len(data)+10
                          rgtp = rgtp + data + self.serial + b'\x00\x00'
                          rgtp[len(rgtp)-2:len(rgtp)] = crc16(rgtp[2:len(rgtp)-2]).to_bytes(length=2,byteorder='big')
                          rgtp = rgtp + b'\x0D\x0A'                          
                          self.sock.send(rgtp)
                          self.serial = ((self.serial[0]*256+self.serial[1]+1)&0xffff).to_bytes(length=2,byteorder='big')     
                          log("Redirect MQTT:%s" %rgtp.hex())
            except Exception as ex:
                log("Redirect MQTT error:"+str(ex))

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
    def __init__(self):
        threading.Thread.__init__(self)
        config_file = os.path.abspath((os.path.dirname(__file__))) + "/config.ini"
        if not os.path.isfile(config_file):
           log("Error: %s does not exist!" % config_file)
           sys.exit(-1)
        cf=configparser.ConfigParser("")
        cf.read(config_file)
        self.host=cf.get("GT2MQTT","host")
        self.port=cf.getint("GT2MQTT","port")
        self.mhost=cf.get("MQTT","host")
        self.mport=cf.getint("MQTT","port")
        self.muser=cf.get("MQTT","user")
        self.mpassword=cf.get("MQTT","password")
        self.pos_home={ 'latitude': 0, 'longitude': 0 }
        self.pos_home['latitude']=cf.getfloat("HOME","latitude")
        self.pos_home['longitude']=cf.getfloat("HOME","longitude")
        self.sock=None
        self.newsock=None
        self.sock=socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        self.sock.bind((self.host,self.port))
        self.sock.setsockopt(socket.SOL_TCP, socket.TCP_NODELAY, 1)
        self.sock.listen(5)
        log("start listen on [%s:%d]." % (self.host,self.port))

    def run(self):
        while True:
            self.newsock,address=self.sock.accept()
            log("new connect from [%s:%s]." %(address[0],address[1]))
            mymqtt = mqtt2(self.mhost, self.mport, self.newsock, self.muser, self.mpassword)
            mymqtt.start()
            p1=pipethread(self.newsock,mymqtt,self.pos_home)
            p1.start()

if __name__=='__main__':
    mapp = s2mqtt()
    mapp.start()


