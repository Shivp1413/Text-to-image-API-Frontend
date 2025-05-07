import streamlit as st
import requests
import os
import json

def setup_sidebar():
    """Setup sidebar with server configuration and model selection options"""
    with st.sidebar:
        st.header("Server Configuration")
        
        # Load saved configuration if exists
        config_file = "config.json"
        if os.path.exists(config_file):
            with open(config_file, "r") as f:
                config = json.load(f)
                default_url = config.get("server_url", "http://127.0.0.1:7860")
        else:
            default_url = "http://127.0.0.1:7860"
            
        sd_server = st.text_input("Automatic1111 API Server URL", default_url)
        
        # Save server URL to session state
        if 'sd_server' not in st.session_state or st.session_state['sd_server'] != sd_server:
            st.session_state['sd_server'] = sd_server
            
            # Save configuration
            with open(config_file, "w") as f:
                json.dump({"server_url": sd_server}, f)
        
        st.info("Make sure the Automatic1111 server is running with the --api and --listen arguments.")
        
        st.header("Model Selection")
        # Get available models (if server is reachable)
        if st.button("Connect to Server"):
            try:
                response = requests.get(f"{sd_server}/sdapi/v1/sd-models")
                if response.status_code == 200:
                    models = [model["title"] for model in response.json()]
                    st.session_state['models'] = models
                    st.session_state['connected'] = True
                    st.success("Successfully connected to Automatic1111 server!")
                    
                    # Get available samplers
                    sampler_response = requests.get(f"{sd_server}/sdapi/v1/samplers")
                    if sampler_response.status_code == 200:
                        samplers = [sampler["name"] for sampler in sampler_response.json()]
                        st.session_state['samplers'] = samplers
                        
                    # Get available upscalers
                    upscalers_response = requests.get(f"{sd_server}/sdapi/v1/upscalers")
                    if upscalers_response.status_code == 200:
                        upscalers = [upscaler["name"] for upscaler in upscalers_response.json()]
                        st.session_state['upscalers'] = upscalers
                        
                    # Get ControlNet models if extension is available
                    try:
                        controlnet_response = requests.get(f"{sd_server}/controlnet/model_list")
                        if controlnet_response.status_code == 200:
                            controlnet_models = [model["model_name"] for model in controlnet_response.json()["model_list"]]
                            st.session_state['controlnet_models'] = controlnet_models
                    except:
                        st.session_state['controlnet_models'] = []
                else:
                    st.warning("Could not connect to Automatic1111 server. Check your server URL and make sure it's running.")
            except Exception as e:
                st.warning(f"Error connecting to server: {e}")
                st.info("Fill in the correct server URL and try again.")
        
        # Only show model selection if we've successfully connected
        if 'connected' in st.session_state and st.session_state['connected']:
            if 'models' in st.session_state:
                selected_model = st.selectbox("Select Model", st.session_state['models'])
                if st.button("Set Model"):
                    try:
                        response = requests.post(
                            f"{sd_server}/sdapi/v1/options", 
                            json={"sd_model_checkpoint": selected_model}
                        )
                        if response.status_code == 200:
                            st.success(f"Model set to: {selected_model}")
                        else:
                            st.error("Failed to set model")
                    except Exception as e:
                        st.error(f"Error setting model: {e}")
                        
            # Advanced settings
            with st.expander("Advanced Settings"):
                # CLIP skip
                clip_skip = st.slider("CLIP Skip", min_value=1, max_value=12, value=1, 
                                      help="Higher values will skip more layers of CLIP text encoder")
                
                # Save or apply advanced settings
                if st.button("Apply Advanced Settings"):
                    try:
                        response = requests.post(
                            f"{sd_server}/sdapi/v1/options", 
                            json={"CLIP_stop_at_last_layers": clip_skip}
                        )
                        if response.status_code == 200:
                            st.success("Advanced settings applied")
                        else:
                            st.error("Failed to apply advanced settings")
                    except Exception as e:
                        st.error(f"Error applying settings: {e}")
        else:
            st.info("Click 'Connect to Server' to fetch available models.")
