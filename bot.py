#!/usr/bin/env python3
"""
Object Detector - Camera-based Object Detection System with Telegram Bot

This script periodically checks a camera endpoint for images, uses image captioning to detect
specified objects, and sends Telegram notifications via Bot API when trigger words are detected.
"""

import os
import sys
import time
import logging
import yaml
import requests
import schedule
import threading
import keyboard
from datetime import datetime
from pathlib import Path
from io import BytesIO
from PIL import Image
from pydantic import BaseModel
from telegram import Bot, ParseMode
from telegram.ext import Updater, CommandHandler
from interrogate import describe_image

# Pydantic model for structured object detection response
class DetectionResult(BaseModel):
    object_detected: bool
    trigger_word: str = ""
    caption: str = ""

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger('object_detector')

class ObjectDetector:
    def __init__(self, config_path="config.yaml"):
        """Initialize the Object Detector application."""
        self.config = self._load_config(config_path)
        self._setup_logging()
        self._setup_directories()
        self.telegram_bot = None
        self.updater = None
        
    def _load_config(self, config_path):
        """Load configuration from YAML file."""
        try:
            with open(config_path, 'r') as file:
                config = yaml.safe_load(file)
            logger.info(f"Configuration loaded from {config_path}")
            return config
        except Exception as e:
            logger.error(f"Failed to load configuration: {e}")
            sys.exit(1)
            
    def _setup_logging(self):
        """Set up file logging based on configuration."""
        if self.config['app'].get('log_file'):
            file_handler = logging.FileHandler(self.config['app']['log_file'])
            file_handler.setFormatter(logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
            logger.addHandler(file_handler)
            
    def _setup_directories(self):
        """Create necessary directories for saving images."""
        if self.config['app'].get('save_detected_images', False):
            Path(self.config['app']['image_save_path']).mkdir(parents=True, exist_ok=True)
            logger.info(f"Created directory for saving detected object images: {self.config['app']['image_save_path']}")
            
    def initialize(self):
        """Initialize Telegram bot."""
        try:
            # Initialize Telegram bot
            logger.info("Initializing Telegram bot")
            self.telegram_bot = Bot(token=self.config['telegram']['bot_token'])
            
            # Set up the updater and dispatcher
            self.updater = Updater(token=self.config['telegram']['bot_token'], use_context=True)
            dispatcher = self.updater.dispatcher
            
            # Register command handlers
            dispatcher.add_handler(CommandHandler("start", self._start_command))
            dispatcher.add_handler(CommandHandler("help", self._help_command))
            dispatcher.add_handler(CommandHandler("status", self._status_command))
            dispatcher.add_handler(CommandHandler("detect", self._detect_command))
            
            # Start the bot
            self.updater.start_polling()
            logger.info("Telegram bot started successfully")
            
            return True
        except Exception as e:
            logger.error(f"Initialization failed: {e}")
            return False
    
    def _start_command(self, update, context):
        """Handle /start command."""
        user_id = update.effective_user.id
        username = update.effective_user.username
        
        # Add user to notify list if not already there
        if 'notify_users' not in self.config['telegram']:
            self.config['telegram']['notify_users'] = []
            
        if user_id not in self.config['telegram']['notify_users']:
            self.config['telegram']['notify_users'].append(user_id)
            update.message.reply_text(
                f"Welcome to the Object Detector Bot! 🔍\n"
                f"You've been added to the notification list.\n"
                f"You'll receive alerts when objects are detected."
            )
        else:
            update.message.reply_text(
                f"Welcome back! You're already on the notification list.\n"
                f"You'll continue to receive alerts when objects are detected."
            )
            
        logger.info(f"User {username} (ID: {user_id}) started the bot")
    
    def _help_command(self, update, context):
        """Handle /help command."""
        update.message.reply_text(
            "🔍 *Object Detector Bot Help* 🔍\n\n"
            "This bot monitors a camera for objects and sends notifications.\n\n"
            "*Commands:*\n"
            "/start - Start receiving notifications\n"
            "/help - Show this help message\n"
            "/status - Check bot status\n"
            "/detect - Trigger manual detection\n",
            parse_mode=ParseMode.MARKDOWN
        )
    
    def _status_command(self, update, context):
        """Handle /status command."""
        trigger_words = ", ".join(self.config['detection']['trigger_words'])
        check_interval = self.config['camera']['check_interval_minutes']
        
        update.message.reply_text(
            "🔍 *Object Detector Status* 🔍\n\n"
            f"*Active trigger words:* {trigger_words}\n"
            f"*Check interval:* {check_interval} minutes\n"
            f"*Camera endpoint:* {self.config['camera']['endpoint']}\n"
            f"*Save detected images:* {self.config['app'].get('save_detected_images', False)}\n",
            parse_mode=ParseMode.MARKDOWN
        )
    
    def _detect_command(self, update, context):
        """Handle /detect command."""
        user_id = update.effective_user.id
        username = update.effective_user.username
        
        update.message.reply_text("🔍 Triggering manual detection...")
        logger.info(f"Manual detection triggered by user {username} (ID: {user_id})")
        
        # Run detection in a separate thread to avoid blocking
        threading.Thread(target=self.check_for_objects, kwargs={'manual': True, 'requested_by': user_id, 'explicit_request': True}).start()
            
    def capture_image(self):
        """Capture image from the camera endpoint."""
        try:
            logger.info(f"Capturing image from {self.config['camera']['endpoint']}")
            response = requests.get(self.config['camera']['endpoint'])
            response.raise_for_status()
            
            # Create a PIL Image from the response content
            image = Image.open(BytesIO(response.content))
            logger.info(f"Image captured successfully: {image.format} {image.size}")
            return response.content
        except Exception as e:
            logger.error(f"Failed to capture image: {e}")
            return None
            
    def detect_object(self, image_data):
        """Detect if any trigger words are present in the image caption."""
        try:
            # Save image data to a temporary file
            temp_file = Path("temp_image.jpg")
            with open(temp_file, "wb") as f:
                f.write(image_data)
            
            # Get image caption using interrogate.py
            logger.info("Generating image caption...")
            caption = describe_image(str(temp_file))
            logger.info(f"Caption: {caption}")
            
            # Check if any trigger words are in the caption
            trigger_words = self.config['detection']['trigger_words']
            caption_lower = caption.lower()
            
            # Split caption into words for whole-word matching
            import re
            caption_words = set(re.findall(r'\b\w+\b', caption_lower))
            
            result = DetectionResult(
                object_detected=False,
                caption=caption
            )
            
            for word in trigger_words:
                # Check if the word appears as a whole word in the caption
                if word.lower() in caption_words:
                    result.object_detected = True
                    result.trigger_word = word
                    logger.info(f"Trigger word '{word}' detected in caption")
                    break
            
            if not result.object_detected:
                logger.info("No trigger words detected in caption")
            
            # Clean up the temporary file
            if temp_file.exists():
                temp_file.unlink()
                
            return result
        except Exception as e:
            logger.error(f"Object detection failed: {e}")
            # Clean up the temporary file in case of error
            temp_file = Path("temp_image.jpg")
            if temp_file.exists():
                temp_file.unlink()
            return DetectionResult(
                object_detected=False,
                caption=f"Error: {str(e)}"
            )
            
    def save_image(self, image_data, detection_result):
        """Save the image."""
        if not self.config['app'].get('save_detected_images', False):
            # Create a temporary file for sending photos even if saving is disabled
            try:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                temp_filepath = Path("temp_detection_image.jpg")
                with open(temp_filepath, 'wb') as f:
                    f.write(image_data)
                return temp_filepath
            except Exception as e:
                logger.error(f"Failed to create temporary image: {e}")
                return None
            
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            trigger_word = detection_result.trigger_word if detection_result.trigger_word else "unknown"
            filename = f"{trigger_word}_{timestamp}.jpg"
            filepath = Path(self.config['app']['image_save_path']) / filename
            
            with open(filepath, 'wb') as f:
                f.write(image_data)
                
            logger.info(f"Image saved to {filepath}")
            return filepath
        except Exception as e:
            logger.error(f"Failed to save image: {e}")
            return None
            
    def send_telegram_notification(self, detection_result, image_path=None, requested_by=None, notify_all=True):
        """Send notification to Telegram users."""
        try:
            # Prepare notification message
            trigger_word = detection_result.trigger_word.upper() if detection_result.trigger_word else "OBJECT"
            message = f"🔍 {trigger_word} DETECTED! 🔍\n"
            message += f"Caption: {detection_result.caption}\n"
            message += f"\nTimestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            
            # If notify_all is False, only send to the requester
            if not notify_all and requested_by:
                # Skip the notification loop for other users - we'll handle the requester separately below
                pass
            else:
                # Send message to each user in the notify list
                for user_id in self.config['telegram']['notify_users']:
                    try:
                        # Skip sending notification to the user who requested it if specified
                        if requested_by and user_id == requested_by:
                            continue
                        
                        logger.info(f"Sending notification to user ID: {user_id}")
                        
                        # Send message
                        self.telegram_bot.send_message(
                            chat_id=user_id,
                            text=message,
                            parse_mode=ParseMode.MARKDOWN
                        )
                        
                        # Send image if available
                        if image_path:
                            with open(image_path, 'rb') as photo:
                                self.telegram_bot.send_photo(
                                    chat_id=user_id,
                                    photo=photo
                                )
                        
                        logger.info(f"Notification sent to user ID: {user_id}")
                    except Exception as e:
                        logger.error(f"Failed to send notification to user ID {user_id}: {e}")
                    
            # If this was a manual detection, also send a response to the requester
            if requested_by:
                try:
                    if detection_result.object_detected:
                        self.telegram_bot.send_message(
                            chat_id=requested_by,
                            text=f"✅ Detection complete: {trigger_word} detected!"
                        )
                        
                        # Send image if available
                        if image_path:
                            with open(image_path, 'rb') as photo:
                                self.telegram_bot.send_photo(
                                    chat_id=requested_by,
                                    photo=photo,
                                    caption=detection_result.caption
                                )
                    else:
                        self.telegram_bot.send_message(
                            chat_id=requested_by,
                            text=f"❌ Detection complete: No {', '.join(self.config['detection']['trigger_words'])} detected.\n\nCaption: {detection_result.caption}"
                        )
                except Exception as e:
                    logger.error(f"Failed to send result to requester {requested_by}: {e}")
                    
            return True
        except Exception as e:
            logger.error(f"Failed to send Telegram notifications: {e}")
            return False
            
    def keyboard_listener(self):
        """Listen for keyboard input to trigger manual object detection."""
        logger.info("Keyboard listener started. Press 'd' to manually trigger object detection.")
        keyboard.add_hotkey('d', self.manual_trigger)
        
    def manual_trigger(self):
        """Manually trigger object detection."""
        logger.info("Manual object detection triggered by keyboard input")
        # Run in a separate thread to avoid blocking the main thread
        threading.Thread(target=self.check_for_objects, kwargs={'manual': True, 'explicit_request': False}).start()
    
    def check_for_objects(self, manual=False, requested_by=None, explicit_request=False):
        """Main function to check for objects and send notifications."""
        if manual:
            logger.info("Starting manual object detection cycle")
        else:
            logger.info("Starting scheduled object detection cycle")
        
        # Capture image
        image_data = self.capture_image()
        if not image_data:
            logger.error("No image captured, skipping detection cycle")
            
            # Notify requester of failure if this was a manual detection
            if requested_by:
                try:
                    self.telegram_bot.send_message(
                        chat_id=requested_by,
                        text="❌ Detection failed: Could not capture image from camera."
                    )
                except Exception as e:
                    logger.error(f"Failed to send failure notification: {e}")
                    
            return
            
        # Detect objects
        detection_result = self.detect_object(image_data)
        
        # Save image regardless of detection result if it's an explicit request
        image_path = None
        if explicit_request or detection_result.object_detected:
            image_path = self.save_image(image_data, detection_result)
        
        # Check if any trigger word was detected
        if detection_result.object_detected:
            # Send notification
            logger.info(f"{detection_result.trigger_word} detected! Sending notifications...")
            # If this is an explicit request, only notify the requester
            if explicit_request and requested_by:
                self.send_telegram_notification(detection_result, image_path, requested_by, notify_all=False)
            else:
                self.send_telegram_notification(detection_result, image_path, requested_by, notify_all=True)
        else:
            logger.info("No trigger words detected in the image.")
            
            # If this was a manual detection, notify the requester
            if requested_by:
                try:
                    message = f"❌ No {', '.join(self.config['detection']['trigger_words'])} detected in the image.\n\nCaption: {detection_result.caption}"
                    self.telegram_bot.send_message(
                        chat_id=requested_by,
                        text=message
                    )
                    
                    # Always send the image if it was an explicit request
                    if explicit_request and image_path:
                        with open(image_path, 'rb') as photo:
                            self.telegram_bot.send_photo(
                                chat_id=requested_by,
                                photo=photo,
                                caption="Current camera view"
                            )
                except Exception as e:
                    logger.error(f"Failed to send negative result notification: {e}")
            
        logger.info("Object detection cycle completed")
    
    def start(self):
        """Start the object detection service."""
        if not self.initialize():
            logger.error("Failed to initialize Object Detector. Exiting.")
            return
            
        # Schedule regular checks
        interval_minutes = self.config['camera'].get('check_interval_minutes', 5)
        logger.info(f"Scheduling object detection every {interval_minutes} minutes")
        schedule.every(interval_minutes).minutes.do(lambda: self.check_for_objects(manual=False, explicit_request=False))
        
        # Start keyboard listener in a separate thread
        keyboard_thread = threading.Thread(target=self.keyboard_listener)
        keyboard_thread.daemon = True  # Thread will exit when main thread exits
        keyboard_thread.start()
        
        # Run once immediately
        logger.info("Running initial object detection")
        self.check_for_objects(manual=False, explicit_request=False)
        
        # Keep the script running
        logger.info("Object Detector is running. Press 'd' to manually trigger object detection. Press Ctrl+C to stop.")
        try:
            # Register signal handlers for graceful shutdown
            import signal
            
            def signal_handler(sig, frame):
                logger.info("Ctrl+C detected, shutting down gracefully...")
                raise KeyboardInterrupt
            
            # Register the signal handler for SIGINT (Ctrl+C)
            signal.signal(signal.SIGINT, signal_handler)
            
            while True:
                schedule.run_pending()
                time.sleep(1)
        except KeyboardInterrupt:
            logger.info("Object Detector stopped by user")
            print("\nShutting down gracefully, please wait...")
        finally:
            # Clean up resources
            try:
                # Stop the keyboard listener
                keyboard.unhook_all()
                logger.info("Keyboard listener stopped")
                
                # Stop the Telegram bot updater
                if self.updater:
                    logger.info("Stopping Telegram bot...")
                    self.updater.stop()
                    logger.info("Telegram bot stopped")
                    
                # Final cleanup
                logger.info("Object Detector shutdown complete")
                print("Shutdown complete. Goodbye!")
            except Exception as e:
                logger.error(f"Error during shutdown: {e}")
                print("Error during shutdown, but exiting anyway.")
                
            # Exit with a clean status code
            import sys
            sys.exit(0)


if __name__ == "__main__":
    print("🔍 Starting Object Detector Bot - Camera-based Detection System 🔍")
    detector = ObjectDetector()
    detector.start()
