# DHCP Monitor for Home Assistant

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/custom-components/hacs)

This Home Assistant integration uses DHCP discovery to monitor IP address assignments on your network. 
It provides 5 sensors showing information about the last 5 detected devices.

## Features
- Detects new IP address assignments via DHCP discovery.
- 5 sensors: `sensor.dhcp_device_1` to `sensor.dhcp_device_5`.
- Attributes include: IP address, MAC address, and Hostname.

## Installation
### HACS
1. Open HACS in Home Assistant.
2. Click on "Integrations".
3. Click the three dots in the top right corner and select "Custom repositories".
4. Add `https://github.com/jonnybergdahl/HomeAssistant_Dhcp_Monitor_Integration` as a "Integration".
5. Click "Add".
6. Search for "DHCP Monitor" and install it.
7. Restart Home Assistant.

### Manual
1. Download the `dhcp_monitor` folder from `custom_components`.
2. Copy it to your Home Assistant `custom_components` directory.
3. Restart Home Assistant.

## Configuration
1. Go to **Settings** > **Devices & Services**.
2. Click **Add Integration**.
3. Search for **DHCP Monitor**.
4. Follow the prompts to complete the setup.

## Usage
The integration will start listening for DHCP discovery events as soon as it is configured.
The sensors will update their state with the IP address of the detected device.
Other details like MAC address and Hostname are available in the sensor attributes.