# Remove later when hosting db later
import os
import time

def cleanup_old_images(image_dir, threshold_days=2):
    """
    Delete images older than the threshold in days from the specified directory.

    :param image_dir: The directory where images are stored.
    :param threshold_days: The age threshold in days; images older than this will be deleted.
    """
    now = time.time()
    threshold_seconds = threshold_days * 86400 # 1 day = 86400 seconds

    for filename in os.listdir(image_dir):
        file_path = os.path.join(image_dir, filename)
        if os.path.isfile(file_path):
            file_age = now - os.path.getmtime(file_path)
            if file_age > threshold_seconds:
                os.remove(file_path)
                print(f"Deleted {file_path} (age: {file_age/86400:.1f} days)")
