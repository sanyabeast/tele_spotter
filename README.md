# 🔍 TeleSpotter

A camera-based object detection system that notifies you via Telegram when specific objects (like cats) are detected in camera images.

## Overview

TeleSpotter periodically captures images from a camera endpoint, uses image captioning to detect specified objects in the image, and sends notifications via Telegram Bot API when trigger words are detected in the caption.

## Features

- 📷 Captures images from a specified camera endpoint
- 🤖 Uses image captioning to detect objects in images
- 🔎 Configurable trigger words for object detection
- 🤖 Interactive Telegram bot with commands
- 📱 Sends Telegram notifications with object descriptions and images
- ⏱️ Configurable check intervals
- 🖼️ Option to save detected object images
- 📝 Comprehensive logging

## Requirements

- Python 3.8+
- A camera endpoint that returns JPEG images (compatible with [cam_point](https://github.com/sanyabeast/cam_point))
- Telegram account and bot token (created via BotFather)

## Installation

1. Clone this repository:
   ```
   git clone https://github.com/yourusername/tele_spotter.git
   cd tele_spotter
   ```

2. Run the setup script to create a virtual environment and install dependencies:
   ```
   python setup.py
   ```

3. Activate the virtual environment:
   - Windows: `venv\Scripts\activate`
   - Linux/Mac: `source venv/bin/activate`

4. Update the `config.yaml` file with your settings:
   - Set your camera endpoint (compatible with [cam_point](https://github.com/sanyabeast/cam_point))
   - Configure your Telegram bot token and user ID
   - Set your trigger words and check interval as needed

## Configuration

Edit `config.yaml` to customize your TeleSpotter:

```yaml
# Camera settings
camera:
  endpoint: "http://192.168.0.102:8080/rear"  # Compatible with cam_point
  check_interval_minutes: 5  # How often to check for objects

# Detection settings
detection:
  trigger_words:
    - "cat"
    - "kitten"

# Telegram notification settings
telegram:
  bot_token: "YOUR_BOT_TOKEN"  # Get from BotFather
  # List of user IDs to notify
  notify_users:
    - 123456789  # Your Telegram user ID

# Application settings
app:
  log_file: "detection_log.log"
  save_detected_images: true
  image_save_path: "detected_objects"
```

## Usage

1. Make sure your camera endpoint is accessible (e.g., [cam_point](https://github.com/sanyabeast/cam_point) is running)
2. Run TeleSpotter:
   ```
   python bot.py
   ```

3. The application will:
   - Start a Telegram bot that listens for commands
   - Check for objects at the specified interval
   - Send Telegram notifications when objects are detected
   - Log all activities to the console and log file

4. Press Ctrl+C to stop the application (graceful shutdown)

## Telegram Bot Commands

TeleSpotter provides a Telegram bot with the following commands:

- `/start` - Start receiving notifications
- `/help` - Show help information
- `/status` - Check current configuration and status
- `/detect` - Trigger a manual detection

To use the bot, search for your bot by username in Telegram and start a conversation with it.

## Troubleshooting

- **Camera Connection Issues**: Verify your camera endpoint is accessible
- **Bot Token Issues**: Make sure your bot token is correct in config.yaml
- **User ID Issues**: Ensure your Telegram user ID is correctly added to the notify_users list
- **Camera Integration**: This project is designed to work with [cam_point](https://github.com/sanyabeast/cam_point) for camera access

## License

MIT
