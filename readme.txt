A python service daemon of gt06, translate the gt06 protocol to mqtt, tested for TUQIANG gt550 car obd gps locator and homeassistant 2023.4.4.

How to use:
   1. modify config.ini;
   2. open the port, set port forwarding;
   3. run gt2mqtt.py(python gt2mqtt.py &);
   4. change the service address and port of gt550;
   5. add device_tracker config in homeassistant's configuration.yaml.
