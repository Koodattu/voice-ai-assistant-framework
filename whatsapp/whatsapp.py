# python
import pyautogui
import time

def safe_locate_center_on_screen(image_path, confidence=0.8):
    try:
        return pyautogui.locateCenterOnScreen(image_path, confidence=confidence)
    except Exception as e:
        #print(f"Error locating image {image_path}: {e}")
        return None

# List of images to check
images_to_check = {
    "accept_call": "./whatsapp/accept_call.png",                # Path to "Answer Call" button
    "accept_video_call": "./whatsapp/accept_video_call.png",       # Path to "Accept Video Call" button
    "update_call_to_video": "./whatsapp/accept_video_call_2.png",   # Path to "Update Call to Video" button
    "in_call": "./whatsapp/e2e.png",                         # Path to "In Call" screen
}

# Initialize call state (False indicates not in a call)
in_call = False

while True:
    # 1. Check for update_call_to_video (applies when in a call)
    update_location = safe_locate_center_on_screen(images_to_check["update_call_to_video"])
    if update_location:
        print(f"Detected update_call_to_video at: {update_location}")
        pyautogui.click(update_location)
        print("Updating call to video!")
        time.sleep(1)

    # 2. Check the in_call screen to update our call state
    in_call_location = safe_locate_center_on_screen(images_to_check["in_call"])
    if in_call_location:
        if not in_call:
            print(f"Detected in_call at: {in_call_location}. Changing state to in call.")
            pyautogui.moveTo(in_call_location)
        in_call = True
    else:
        if in_call:
            print("in_call not detected. Changing state to not in call.")
        in_call = False

    # 3. If not in a call, check for accept_call
    if not in_call:
        accept_call_location = safe_locate_center_on_screen(images_to_check["accept_call"])
        if accept_call_location:
            print(f"Detected accept_call at: {accept_call_location}")
            pyautogui.click(accept_call_location)
            print("Accepting call!")
            in_call = True
            time.sleep(1)
        else:
            # 4. Then check for accept_video_call
            accept_video_call_location = safe_locate_center_on_screen(images_to_check["accept_video_call"])
            if accept_video_call_location:
                print(f"Detected accept_video_call at: {accept_video_call_location}")
                pyautogui.click(accept_video_call_location)
                print("Accepting video call!")
                in_call = True
                time.sleep(1)
    
    print(f"Currently in a call: {in_call}. Waiting for next check...")
    time.sleep(1)