
# Meshtastic Repeater & Alert GUI

A Meshtastic-based emergency repeater interface with real-time alerts, weather integration, and message broadcasting.

🛠️ Designed by **Diogenes**  
🖥️ Platform: Windows  
📡 Uses: Meshtastic serial interface (USB)

## Features

- 🔔 Sound notifications for key events
- 🛰️ Manual and scheduled Station ID with philosophical quotes
- 🌩️ NWS Weather Alert integration (default: Pulaski County, Arkansas)
- 📝 GUI for sending and receiving text messages
- 💬 Repeater-friendly operation

## Requirements

- Windows 10/11
- Python 3.11+
- A Meshtastic-compatible device connected via COM port (default: COM11)

## Setup Instructions

1. Clone or download this repository.

2. Install Python dependencies:
  
   pip install -r requirements.txt
   

3. Run the GUI:
   
   python alertWinSound.py
   

## Configuration

To change the COM port:
Edit this line in `alertWinSound.py`:

self.meshInterface = meshtastic.serial_interface.SerialInterface(devPath="COM11")


To change the NWS weather zone (default is Pulaski County):

NWS_ZONE = "ARC119"


## Quotes Attribution

All Station ID quotes are from classical philosophers, primarily **Diogenes**.

## License

Distributed under the [MIT License](LICENSE). Use, modify, and share freely.

> “I threw away my cup when I saw a child drinking from his hands.” — *Diogenes*
