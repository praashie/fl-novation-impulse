from flatmate import version_string as flatmate_version

header = "=" * 80

message = f"""
    MIDI Script for Novation Impulse 25/49/61 by Praash
    Version: 0.5.0
    Flatmate version: {flatmate_version}

    Get updates and report issues at GitHub:
    https://github.com/praashie/fl-novation-impulse/

    IL forum thread:
    https://forum.image-line.com/viewtopic.php?f=1994&t=229878&p=1500428
"""

def print_debug_info():
    print(header)
    print(message)
    print(header)
