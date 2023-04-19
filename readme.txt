A python service daemon of gt06, translate the gt06 protocol to mqtt, tested for TUQIANG gt550 car obd gps locator and homeassistant 2023.4.4.

How to use:
   1. modify config.ini;
   2. add home coordinate adn amap key in gt2mqtt.py;
   3. open the port, set port forwarding;
   4. run gt2mqtt.py(python gt2mqtt.py &);
   5. change the service address and port of gt550;
   6. add device_tracker config in homeassistant's configuration.yaml.
