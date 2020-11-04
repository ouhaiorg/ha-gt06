# ha-gt06
a homeassistant device_tracker component for gt06,tested for TUQIANG gt550 car obd gps locator
include a gt06 service and a coordinate transformation(WGS86 to GCJ02).

How to use:
1. Copy ha-gt06 directory(two files) to the directory of homeassistant component;
2. Add to homeassistant config file:
device_tracker:
  - platform: ha-gt06
    host: 192.168.X.X
    port: 5035
3. Open 5035 port and set port forwarding;
4. Change the service address of gt550.
