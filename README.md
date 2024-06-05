# About
A Czech card game "Prší" made in python.

Utilizes python's builtin [socket library](https://docs.python.org/3/library/socket.html) to allow two players on the same network to play against eachother.

# Usage
Run two instances of main.py and select "Host game" on one and "Join game" on the other.

# Settings
Edit resources/options.json to change settings. The settings are loaded when the program starts
## lang
Determines which language should the program use.
Languages are defined in resources/lang.
You can add your own .json file to resources/lang/ and then set the filename (without .json) as the lang setting to use that language.
## localhost
Can be either _true_ or _false_.

When _true_, localhost IP address will be used to host a game.

When _false_, the program will attempt to determine the device's network address automatically.
