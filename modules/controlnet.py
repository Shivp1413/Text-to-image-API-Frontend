import streamlit as st
import requests
import base64
from io import BytesIO
from PIL import Image

def show_controlnet_tab():
    """Display the ControlNet tab with all its UI elements and functionality"""
    st.header("ControlNet")
    
    # Get server URL from session state
    sd_server = st.session_state.get('sd_server', "http://127.0.0.1:7860")
    
    # Check if ControlNet is available
    if 'controlnet_models' not in st.session_state or not st.session_state['controlnet_models']:
        st.warning("ControlNet extension not detected on the server. Please make sure it's installed.")
        st.info("You can install ControlNet from the Extensions tab in the Automatic1111 WebUI.")
        return
    
    # Main UI
    controlnet_models = st.session_state.get('controlnet_models', [])
    
    # Upload control image
    uploaded_control_image = st.file_uploader("Upload Control Image", type=["png", "jpg", "jpeg"], key="controlnet_upload")
    
    if uploaded_control_image is not None:
        control_image = Image.open(uploaded_control_image)
        
        # Display control image
        st.image(control_image, caption="Control Image", use_column_width=True)
        
        # ControlNet settings
        with st.expander("ControlNet Settings", expanded=True):
            col1, col2 = st.columns(2)
            
            with col1:
                # Model selection
                selected_model = st.selectbox("ControlNet Model", controlnet_models)
                
                # Pre-processor
                preprocessors = [
                    "none", "canny", "depth", "depth_leres", "depth_leres++", 
                    "hed", "mlsd", "normal_map", "openpose", "openpose_hand", 
                    "pidinet", "scribble", "fake_scribble", "segmentation"
                ]
                preprocessor = st.selectbox("Preprocessor", preprocessors)
                
            with col2:
                # Control parameters
                control_weight = st.slider("Control Weight", min_value=0.0, max_value=1.0, value=1.0, step=0.05)
                guidance_start = st.slider("Guidance Start", min_value=0.0, max_value=1.0, value=0.0, step=0.05)
                guidance_end = st.slider("Guidance End", min_value=0.0, max_value=1.0, value=1.0, step=0.05)
                
                # Advanced options
                advanced_options = st.checkbox("Show Advanced Options")
            
            if advanced_options:
                col3, col4 = st.columns(2)
                
                with col3:
                    control_mode = st.selectbox("Control Mode", [
                        "Balanced", "My prompt is more important", "ControlNet is more important"
                    ])
                    
                    # Map mode selection to actual values
                    control_mode_map = {
                        "Balanced": 0,
                        "My prompt is more important": 1,
                        "ControlNet is more important": 2
                    }
                    
                    resize_mode = st.selectbox("Resize Mode", [
                        "Just Resize", "Crop and Resize", "Resize and Fill"
                    ])
                    
                    # Map resize mode to actual values
                    resize_mode_map = {
                        "Just Resize": 0,
                        "Crop and Resize": 1,
                        "Resize and Fill": 2
                    }
                
                with col4:
                    lowvram = st.checkbox("Low VRAM", value=False)
                    pixel_perfect = st.checkbox("Pixel Perfect", value=False)
            else:
                # Default values
                control_mode_map = {"Balanced": 0}
                control_mode = "Balanced"
                resize_mode_map = {"Just Resize": 0}
                resize_mode = "Just Resize"
                lowvram = False
                pixel_perfect = False
        
        # Prompt inputs
        st.subheader("Generation Parameters")
        prompt = st.text_area("Prompt", "A beautiful landscape with mountains and a lake, photorealistic, detailed", key="controlnet_prompt")
        negative_prompt = st.text_area("Negative Prompt", "blurry, low quality, deformed, ugly", key="controlnet_neg_prompt")
        
        # Generation parameters
        col1, col2, col3 = st.columns(3)
        with col1:
            width = st.number_input("Width", min_value=64, max_value=2048, value=512, step=64, key="controlnet_width")
            steps = st.number_input("Steps", min_value=1, max_value=150, value=20, key="controlnet_steps")
        
        with col2:
            height = st.number_input("Height", min_value=64, max_value=2048, value=512, step=64, key="controlnet_height")
            seed = st.number_input("Seed", min_value=-1, value=-1, key="controlnet_seed")
        
        with col3:
            samplers = st.session_state.get('samplers', [
                "Euler a", "Euler", "LMS", "Heun", "DPM2", "DPM2 a", "DPM++ 2S a", 
                "DPM++ 2M", "DPM++ SDE", "DPM fast", "DPM adaptive", "LMS Karras", 
                "DPM2 Karras", "DPM2 a Karras", "DPM++ 2S a Karras", "DPM++ 2M Karras", 
                "DPM++ SDE Karras", "DDIM", "PLMS"
            ])
            sampler = st.selectbox("Sampler", samplers, index=0, key="controlnet_sampler")
            cfg_scale = st.number_input("CFG Scale", min_value=1.0, max_value=30.0, value=7.0, step=0.5, key="controlnet_cfg")
        
        # Generate button
        if st.button("Generate Image with ControlNet", key="controlnet_generate"):
            with st.spinner("Preprocessing and generating image..."):
                # Convert control image to base64
                buffered = BytesIO()
                control_image.save(buffered, format="PNG")
                img_base64 = base64.b64encode(buffered.getvalue()).decode("utf-8")
                
                # Prepare controlnet units
                controlnet_unit = {
                    "input_image": f"data:image/png;base64,{img_base64}",
                    "model": selected_model,
                    "weight": control_weight,
                    "guidance_start": guidance_start,
                    "guidance_end": guidance_end,
                    "processor_res": max(width, height),  # Use the larger dimension
                    "threshold_a": 64,  # Default value for most preprocessors
                    "threshold_b": 64,  # Default value for most preprocessors
                    "module": preprocessor,
                    "control_mode": control_mode_map[control_mode],
                    "resize_mode": resize_mode_map[resize_mode],
                    "pixel_perfect": pixel_perfect,
                    "lowvram": lowvram
                }
                
                # Create main payload
                payload = {
                    "prompt": prompt,
                    "negative_prompt": negative_prompt,
                    "width": width,
                    "height": height,
                    "steps": steps,
                    "cfg_scale": cfg_scale,
                    "sampler_name": sampler,
                    "seed": seed,
                    "alwayson_scripts": {
                        "controlnet": {
                            "args": [controlnet_unit]
                        }
                    }
                }
                
                try:
                    # Make API call to generate the image
                    response = requests.post(f"{sd_server}/sdapi/v1/txt2img", json=payload)
                    
                    if response.status_code == 200:
                        r = response.json()
                        
                        # Display generated image
                        for i, img_data in enumerate(r['images']):
                            # Skip control net visualization images (every second image)
                            if i % 2 == 0:  # Only process the actual generated images
                                image = Image.open(BytesIO(base64.b64decode(img_data.split(",", 1)[0])))
                                st.image(image, caption="Generated Image", use_column_width=True)
                                
                                # Add a download button
                                buf = BytesIO()
                                image.save(buf, format="PNG")
                                byte_im = buf.getvalue()
                                st.download_button(
                                    label="Download Image",
                                    data=byte_im,
                                    file_name=f"controlnet_generated_image.png",
                                    mime="image/png",
                                    key=f"download_controlnet"
                                )
                    else:
                        st.error(f"Error: {response.status_code}, {response.text}")
                except Exception as e:
                    st.error(f"Error generating image: {e}")
                    st.info("Make sure the ControlNet extension is properly installed and the server is running.")
    else:
        st.info("Please upload a control image to start. The image will guide the generation process based on the ControlNet model you select.")
        
        # Show examples of what ControlNet can do
        with st.expander("What is ControlNet?"):
            st.markdown("""
            **ControlNet** allows you to control the image generation process using input images. For example:
            
            - Use sketch images to generate detailed pictures
            - Use pose estimation to control character positions
            - Use canny edge detection to maintain structural elements
            - Use depth maps to control perspective and spatial layout
            
            Each ControlNet model is trained for a specific type of control. Upload an image and select the appropriate model to get started.
            """)
