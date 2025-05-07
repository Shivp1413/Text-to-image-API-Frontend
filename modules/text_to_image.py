import streamlit as st
import requests
import base64
from io import BytesIO
from PIL import Image

def show_text_to_image_tab():
    """Display the Text to Image tab with all its UI elements and functionality"""
    st.header("Text to Image")
    
    # Get server URL from session state
    sd_server = st.session_state.get('sd_server', "http://127.0.0.1:7860")
    
    # Prompt inputs
    prompt = st.text_area("Prompt", "A beautiful landscape with mountains and a lake, photorealistic, detailed")
    negative_prompt = st.text_area("Negative Prompt", "blurry, low quality, deformed, ugly")
    
    # Template selector
    with st.expander("Prompt Templates", expanded=False):
        templates = {
            "None": {"prompt": "", "negative": ""},
            "Photorealistic": {"prompt": "photorealistic, 8k, detailed, sharp focus", 
                              "negative": "cartoon, drawing, anime, illustration, painting"},
            "Anime Style": {"prompt": "anime style, vibrant colors, detailed, illustration", 
                           "negative": "photorealistic, 3d, photograph, realistic"},
            "Oil Painting": {"prompt": "oil painting, detailed brushwork, artistic, textured canvas", 
                            "negative": "digital art, 3d, photograph, sharp edges"}
        }
        
        selected_template = st.selectbox("Select Template", list(templates.keys()))
        
        if selected_template != "None" and st.button("Apply Template"):
            # Append template to current prompts
            if prompt:
                prompt += ", " + templates[selected_template]["prompt"]
            else:
                prompt = templates[selected_template]["prompt"]
                
            if negative_prompt:
                negative_prompt += ", " + templates[selected_template]["negative"]
            else:
                negative_prompt = templates[selected_template]["negative"]
                
            # Force refresh of text areas
            st.experimental_set_query_params()
    
    # Generation parameters
    col1, col2, col3 = st.columns(3)
    with col1:
        width = st.number_input("Width", min_value=64, max_value=2048, value=512, step=64)
        steps = st.number_input("Steps", min_value=1, max_value=150, value=20)
        cfg_scale = st.number_input("CFG Scale", min_value=1.0, max_value=30.0, value=7.0, step=0.5)
    
    with col2:
        height = st.number_input("Height", min_value=64, max_value=2048, value=512, step=64)
        seed = st.number_input("Seed", min_value=-1, value=-1)
        batch_size = st.number_input("Batch Size", min_value=1, max_value=4, value=1)
    
    with col3:
        samplers = st.session_state.get('samplers', [
            "Euler a", "Euler", "LMS", "Heun", "DPM2", "DPM2 a", "DPM++ 2S a", 
            "DPM++ 2M", "DPM++ SDE", "DPM fast", "DPM adaptive", "LMS Karras", 
            "DPM2 Karras", "DPM2 a Karras", "DPM++ 2S a Karras", "DPM++ 2M Karras", 
            "DPM++ SDE Karras", "DDIM", "PLMS"
        ])
        sampler = st.selectbox("Sampler", samplers, index=0)
        restore_faces = st.checkbox("Restore Faces", value=False)
        tiling = st.checkbox("Tiling", value=False)
    
    # Advanced options
    with st.expander("Advanced Options", expanded=False):
        enable_hr = st.checkbox("High Resolution Fix", value=False)
        if enable_hr:
            hr_scale = st.slider("Upscale by", min_value=1.0, max_value=4.0, value=2.0, step=0.1)
            hr_upscaler = st.selectbox("Upscaler", 
                                      ["Latent", "Nearest", "ESRGAN_4x", "LDSR", "R-ESRGAN 4x+", "ScuNET GAN"],
                                      index=0)
            hr_second_pass_steps = st.slider("HR Steps", min_value=0, max_value=150, value=0)
        
    # Generate button
    if st.button("Generate Image", key="txt2img_generate"):
        with st.spinner("Generating image..."):
            payload = {
                "prompt": prompt,
                "negative_prompt": negative_prompt,
                "width": width,
                "height": height,
                "steps": steps,
                "cfg_scale": cfg_scale,
                "sampler_name": sampler,
                "seed": seed,
                "batch_size": batch_size,
                "restore_faces": restore_faces,
                "tiling": tiling
            }
            
            # Add high-res options if enabled
            if enable_hr:
                payload.update({
                    "enable_hr": True,
                    "hr_scale": hr_scale,
                    "hr_upscaler": hr_upscaler,
                    "hr_second_pass_steps": hr_second_pass_steps if hr_second_pass_steps > 0 else steps
                })
            
            try:
                response = requests.post(f"{sd_server}/sdapi/v1/txt2img", json=payload)
                
                if response.status_code == 200:
                    r = response.json()
                    
                    # Create columns for multiple images
                    if batch_size > 1:
                        img_columns = st.columns(min(batch_size, 4))  # Max 4 columns
                    
                    for i, img_data in enumerate(r['images']):
                        image = Image.open(BytesIO(base64.b64decode(img_data.split(",", 1)[0])))
                        
                        # If multiple images, use columns
                        if batch_size > 1:
                            col_idx = i % len(img_columns)
                            with img_columns[col_idx]:
                                st.image(image, caption=f"Image {i+1}", use_column_width=True)
                                
                                # Add a download button
                                buf = BytesIO()
                                image.save(buf, format="PNG")
                                byte_im = buf.getvalue()
                                st.download_button(
                                    label="Download",
                                    data=byte_im,
                                    file_name=f"generated_image_{i+1}.png",
                                    mime="image/png",
                                    key=f"download_{i+1}"
                                )
                        else:
                            # Single image - use full width
                            st.image(image, caption="Generated Image", use_column_width=True)
                            
                            # Add download and info buttons
                            col1, col2 = st.columns(2)
                            
                            # Download button
                            buf = BytesIO()
                            image.save(buf, format="PNG")
                            byte_im = buf.getvalue()
                            
                            with col1:
                                st.download_button(
                                    label="Download Image",
                                    data=byte_im,
                                    file_name="generated_image.png",
                                    mime="image/png"
                                )
                            
                            with col2:
                                if st.button("View Generation Info"):
                                    # Display generation parameters
                                    st.json(r['parameters'])
                else:
                    st.error(f"Error: {response.status_code}, {response.text}")
            except Exception as e:
                st.error(f"Error: {e}")
