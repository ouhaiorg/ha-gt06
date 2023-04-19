gt06 daemon can translate the gt06 protocol to MQTT protocol, use for a device tracker in homeassistant, have tested by TUQIANG gt550 car obd gps locator and homeassistant 2023.4.4.

How to use:
   1. modify config.ini;
   2. open the internet port or set port forwarding;
   3. run gt2mqtt.py(python gt2mqtt.py &);
   4. change the service address and port of gt550;
   5. add device_tracker config in homeassistant's configuration.yaml.
