# Import all modules to make them available when importing the package
from modules.server_config import setup_sidebar
from modules.text_to_image import show_text_to_image_tab
from modules.image_to_image import show_image_to_image_tab
from modules.upscaler import show_upscaler_tab
from modules.controlnet import show_controlnet_tab