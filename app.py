import streamlit as st
from modules.text_to_image import show_text_to_image_tab
from modules.image_to_image import show_image_to_image_tab
from modules.upscaler import show_upscaler_tab
from modules.controlnet import show_controlnet_tab
from modules.server_config import setup_sidebar

st.set_page_config(page_title="Stable Diffusion Frontend", layout="wide")

# Title
st.title("Stable Diffusion API Frontend")

# Setup sidebar for server configuration and model selection
setup_sidebar()

# Main content area with tabs
tab1, tab2, tab3, tab4 = st.tabs(["Text to Image", "Image to Image", "Upscaler", "ControlNet"])

with tab1:
    show_text_to_image_tab()

with tab2:
    show_image_to_image_tab()

with tab3:
    show_upscaler_tab()

with tab4:
    show_controlnet_tab()

# Footer
st.markdown("---")
st.markdown("Stable Diffusion Frontend powered by Streamlit")
