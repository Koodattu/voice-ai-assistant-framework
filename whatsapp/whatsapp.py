# whatsapp.py
import pyautogui
import time
import uuid
from logger import logger

def safe_locate_center_on_screen(image_path, confidence=0.8):
    try:
        return pyautogui.locateCenterOnScreen(image_path, confidence=confidence)
    except Exception as e:
        #logger.error(f"WhatsApp: Error locating image {image_path}: {e}")
        return None

def run_whatsapp(state):
    logger.info("WhatsApp: Starting WhatsApp thread.")
    images_to_check = {
        "accept_call": "./whatsapp/accept_call.png",                
        "accept_video_call": "./whatsapp/accept_video_call.png",       
        "update_call_to_video": "./whatsapp/accept_video_call_2.png",   
        "in_call": "./whatsapp/e2e.png",                             
    }
    while not state.shutdown:
        # 1. Check for update_call_to_video (if already in a call)
        update_location = safe_locate_center_on_screen(images_to_check["update_call_to_video"])
        if update_location:
            logger.info(f"WhatsApp: Detected update_call_to_video at: {update_location}")
            pyautogui.click(update_location)
            logger.info("WhatsApp: Updating call to video!")
            time.sleep(1)

        # 2. Check the in_call screen to update our call state
        in_call_location = safe_locate_center_on_screen(images_to_check["in_call"])
        current_call_state = True if in_call_location else False

        # If we have just entered a call, generate a new GUID for this call.
        if current_call_state and not state.in_call:
            if state.current_call_id is None:
                state.current_call_id = str(uuid.uuid4())
                logger.info(f"WhatsApp: New call detected. Generated call_id: {state.current_call_id}")
            else:
                logger.info(f"WhatsApp: Call resumed with existing call_id: {state.current_call_id}")
        elif not current_call_state and state.in_call:
            logger.info("WhatsApp: Call ended. Resetting call state.")
            # Clear conversation history and reset the call id when call ends.
            state.clear_conversation_history()

        state.in_call = current_call_state

        # 3. If not in a call, check for an incoming call
        if not state.in_call:
            accept_call_location = safe_locate_center_on_screen(images_to_check["accept_call"])
            if accept_call_location:
                logger.info(f"WhatsApp: Detected accept_call at: {accept_call_location}")
                pyautogui.click(accept_call_location)
                logger.info("WhatsApp: Accepting call!")
                state.in_call = True
                # Generate a new call ID if none exists
                if state.current_call_id is None:
                    state.current_call_id = str(uuid.uuid4())
                    logger.info(f"WhatsApp: Generated call_id: {state.current_call_id}")
                time.sleep(1)
            else:
                accept_video_call_location = safe_locate_center_on_screen(images_to_check["accept_video_call"])
                if accept_video_call_location:
                    logger.info(f"WhatsApp: Detected accept_video_call at: {accept_video_call_location}")
                    pyautogui.click(accept_video_call_location)
                    logger.info("WhatsApp: Accepting video call!")
                    state.in_call = True
                    if state.current_call_id is None:
                        state.current_call_id = str(uuid.uuid4())
                        logger.info(f"WhatsApp: Generated call_id: {state.current_call_id}")
                    time.sleep(1)

        logger.info(f"WhatsApp: Currently in a call: {state.in_call}. Waiting for next check...")
        time.sleep(1)
