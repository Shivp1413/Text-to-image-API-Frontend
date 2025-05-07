import streamlit as st
import requests
import base64
from io import BytesIO
from PIL import Image

def show_image_to_image_tab():
    """Display the Image to Image tab with all its UI elements and functionality"""
    st.header("Image to Image")
    
    # Get server URL from session state
    sd_server = st.session_state.get('sd_server', "http://127.0.0.1:7860")
    
    # Upload image
    uploaded_image = st.file_uploader("Upload an image", type=["png", "jpg", "jpeg"])
    
    # Image preprocessing options
    if uploaded_image is not None:
        image = Image.open(uploaded_image)
        
        # Display image with options
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.image(image, caption="Uploaded Image", use_column_width=True)
            
        with col2:
            with st.expander("Image Preprocessing", expanded=True):
                resize_factor = st.slider("Resize Factor", min_value=0.1, max_value=2.0, value=1.0, step=0.1)
                
                if resize_factor != 1.0 and st.button("Resize Image"):
                    new_width = int(image.width * resize_factor)
                    new_height = int(image.height * resize_factor)
                    image = image.resize((new_width, new_height), Image.LANCZOS)
                    st.session_state['processed_image'] = image
                    st.success(f"Image resized to {new_width}x{new_height} pixels")
        
        # Save processed image to session state
        if 'processed_image' not in st.session_state:
            st.session_state['processed_image'] = image
        
        # Prompt inputs
        prompt_img2img = st.text_area("Prompt", "A beautiful landscape with mountains and a lake, photorealistic, detailed", key="img2img_prompt")
        negative_prompt_img2img = st.text_area("Negative Prompt", "blurry, low quality, deformed, ugly", key="img2img_neg_prompt")
        
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
            
            selected_template = st.selectbox("Select Template", list(templates.keys()), key="img2img_template")
            
            if selected_template != "None" and st.button("Apply Template", key="img2img_apply_template"):
                # Append template to current prompts
                if prompt_img2img:
                    prompt_img2img += ", " + templates[selected_template]["prompt"]
                else:
                    prompt_img2img = templates[selected_template]["prompt"]
                    
                if negative_prompt_img2img:
                    negative_prompt_img2img += ", " + templates[selected_template]["negative"]
                else:
                    negative_prompt_img2img = templates[selected_template]["negative"]
        
        # Generation parameters
        col1, col2, col3 = st.columns(3)
        with col1:
            denoising_strength = st.slider("Denoising Strength", min_value=0.0, max_value=1.0, value=0.75, step=0.05)
            steps_img2img = st.number_input("Steps", min_value=1, max_value=150, value=20, key="img2img_steps")
            cfg_scale_img2img = st.number_input("CFG Scale", min_value=1.0, max_value=30.0, value=7.0, step=0.5, key="img2img_cfg")
        
        with col2:
            # Use original image dimensions by default
            width_img2img = st.number_input("Width", min_value=64, max_value=2048, value=st.session_state['processed_image'].width, step=64, key="img2img_width")
            height_img2img = st.number_input("Height", min_value=64, max_value=2048, value=st.session_state['processed_image'].height, step=64, key="img2img_height")
            seed_img2img = st.number_input("Seed", min_value=-1, value=-1, key="img2img_seed")
        
        with col3:
            samplers = st.session_state.get('samplers', [
                "Euler a", "Euler", "LMS", "Heun", "DPM2", "DPM2 a", "DPM++ 2S a", 
                "DPM++ 2M", "DPM++ SDE", "DPM fast", "DPM adaptive", "LMS Karras", 
                "DPM2 Karras", "DPM2 a Karras", "DPM++ 2S a Karras", "DPM++ 2M Karras", 
                "DPM++ SDE Karras", "DDIM", "PLMS"
            ])
            sampler_img2img = st.selectbox("Sampler", samplers, index=0, key="img2img_sampler")
            restore_faces_img2img = st.checkbox("Restore Faces", value=False, key="img2img_restore_faces")
            tiling_img2img = st.checkbox("Tiling", value=False, key="img2img_tiling")
        
        # Generation modes
        img2img_mode = st.radio("Generation Mode", ["Standard", "Inpainting", "Outpainting"], horizontal=True)
        
        if img2img_mode == "Inpainting":
            st.info("Inpainting mode: Please use the Automatic1111 UI for inpainting as it requires complex image masking capabilities.")
            
        elif img2img_mode == "Outpainting":
            outpainting_direction = st.selectbox("Outpainting Direction", 
                                               ["Left", "Right", "Top", "Bottom", "All Directions"],
                                               index=4)
            outpainting_pixels = st.slider("Pixels to Extend", min_value=32, max_value=512, value=128, step=32)
            
        # Generate button
        if st.button("Generate Image", key="img2img_generate"):
            with st.spinner("Generating image..."):
                # Convert image to base64
                buffered = BytesIO()
                st.session_state['processed_image'].save(buffered, format="PNG")
                img_base64 = base64.b64encode(buffered.getvalue()).decode("utf-8")
                
                # Basic payload
                payload = {
                    "init_images": [f"data:image/png;base64,{img_base64}"],
                    "prompt": prompt_img2img,
                    "negative_prompt": negative_prompt_img2img,
                    "denoising_strength": denoising_strength,
                    "width": width_img2img,
                    "height": height_img2img,
                    "steps": steps_img2img,
                    "cfg_scale": cfg_scale_img2img,
                    "sampler_name": sampler_img2img,
                    "seed": seed_img2img,
                    "restore_faces": restore_faces_img2img,
                    "tiling": tiling_img2img
                }
                
                # Modify payload for outpainting
                if img2img_mode == "Outpainting":
                    # This is a simplified approach; actual outpainting might require more complex handling
                    # For a full implementation, you might need to adjust the canvas size and positioning
                    if outpainting_direction == "Left":
                        payload["width"] = width_img2img + outpainting_pixels
                    elif outpainting_direction == "Right":
                        payload["width"] = width_img2img + outpainting_pixels
                    elif outpainting_direction == "Top":
                        payload["height"] = height_img2img + outpainting_pixels
                    elif outpainting_direction == "Bottom":
                        payload["height"] = height_img2img + outpainting_pixels
                    elif outpainting_direction == "All Directions":
                        payload["width"] = width_img2img + outpainting_pixels * 2
                        payload["height"] = height_img2img + outpainting_pixels * 2
                    
                    # For outpainting, use higher denoising strength
                    payload["denoising_strength"] = max(0.8, denoising_strength)
                
                try:
                    response = requests.post(f"{sd_server}/sdapi/v1/img2img", json=payload)
                    
                    if response.status_code == 200:
                        r = response.json()
                        for i, img_data in enumerate(r['images']):
                            image = Image.open(BytesIO(base64.b64decode(img_data.split(",", 1)[0])))
                            st.image(image, caption=f"Generated Image {i+1}", use_column_width=True)
                            
                            # Add a download button
                            buf = BytesIO()
                            image.save(buf, format="PNG")
                            byte_im = buf.getvalue()
                            st.download_button(
                                label="Download Image",
                                data=byte_im,
                                file_name=f"generated_image_img2img_{i+1}.png",
                                mime="image/png",
                                key=f"download_img2img_{i+1}"
                            )
                    else:
                        st.error(f"Error: {response.status_code}, {response.text}")
                except Exception as e:
                    st.error(f"Error: {e}")
    else:
        st.info("Please upload an image to start.")
