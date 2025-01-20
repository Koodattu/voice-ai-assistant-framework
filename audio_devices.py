import sounddevice as sd

# Get the list of audio devices
devices = sd.query_devices()
hostapis = sd.query_hostapis()

# Translate hostapi index to meaningful name
def get_hostapi_name(index):
    return hostapis[index]['name'] if index < len(hostapis) else "Unknown"

print("Audio Input Devices:")
for index, device in enumerate(devices):
    if device['max_input_channels'] > 0:  # Check for input devices
        hostapi_name = get_hostapi_name(device['hostapi'])
        print(f"{index}: {hostapi_name}: {device['name']}")

print("\nAudio Output Devices:")
for index, device in enumerate(devices):
    if device['max_output_channels'] > 0:  # Check for output devices
        hostapi_name = get_hostapi_name(device['hostapi'])
        print(f"{index}: {hostapi_name}: {device['name']}")
