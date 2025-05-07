import streamlit as st
import requests
import base64
from io import BytesIO
from PIL import Image

def show_upscaler_tab():
    """Display the Upscaler tab with all its UI elements and functionality"""
    st.header("Image Upscaler")
    
    # Get server URL from session state
    sd_server = st.session_state.get('sd_server', "http://127.0.0.1:7860")
    
    # Upload image
    uploaded_image = st.file_uploader("Upload an image to upscale", type=["png", "jpg", "jpeg"], key="upscaler_upload")
    
    if uploaded_image is not None:
        image = Image.open(uploaded_image)
        
        # Display original image
        st.image(image, caption="Original Image", use_column_width=True)
        
        # Get image dimensions
        st.text(f"Original dimensions: {image.width} x {image.height} pixels")
        
        # Upscaler options
        col1, col2 = st.columns(2)
        
        with col1:
            # Get upscalers from session state or use defaults
            upscalers = st.session_state.get('upscalers', [
                "Lanczos", "Nearest", "ESRGAN_4x", "R-ESRGAN 4x+", "ScuNET GAN"
            ])
            
            selected_upscaler = st.selectbox("Upscaler", upscalers)
            
        with col2:
            upscale_factor = st.slider("Upscale Factor", min_value=1.0, max_value=4.0, value=2.0, step=0.5)
        
        # Additional options
        resize_mode = st.radio("Resize Mode", ["Scale from original", "Target resolution"], horizontal=True)
        
        if resize_mode == "Target resolution":
            target_col1, target_col2 = st.columns(2)
            with target_col1:
                target_width = st.number_input("Target Width", min_value=image.width, max_value=4096, value=image.width*2)
            with target_col2:
                target_height = st.number_input("Target Height", min_value=image.height, max_value=4096, value=image.height*2)
                
        # Face restoration option
        face_restoration = st.checkbox("Restore Faces", value=False)
        
        if face_restoration:
            face_restorer = st.selectbox("Face Restoration Model", 
                                       ["CodeFormer", "GFPGAN"], 
                                       index=0)
            if face_restorer == "CodeFormer":
                codeformer_weight = st.slider("CodeFormer Weight", min_value=0.0, max_value=1.0, value=0.75, step=0.05,
                                           help="0 = Maximum effect, 1 = Minimum effect")
        
        # Upscale button
        if st.button("Upscale Image", key="upscale_button"):
            with st.spinner("Upscaling image... This may take a while depending on image size"):
                # Convert image to base64
                buffered = BytesIO()
                image.save(buffered, format="PNG")
                img_base64 = base64.b64encode(buffered.getvalue()).decode("utf-8")
                
                # Calculate target dimensions
                if resize_mode == "Scale from original":
                    target_width = int(image.width * upscale_factor)
                    target_height = int(image.height * upscale_factor)
                
                # Create payload
                payload = {
                    "image": f"data:image/png;base64,{img_base64}",
                    "upscaler_1": selected_upscaler,
                    "upscaler_2": "None",
                    "upscaler_2_visibility": 0,
                    "resize_mode": 0,  # 0 = Just resize, 1 = Crop and resize, 2 = Resize and fill
                    "width": target_width,
                    "height": target_height,
                    "upscaling_resize": upscale_factor if resize_mode == "Scale from original" else -1,
                }
                
                # Add face restoration if selected
                if face_restoration:
                    payload["enable_face_restoration"] = True
                    payload["face_restorer"] = face_restorer
                    if face_restorer == "CodeFormer":
                        payload["codeformer_weight"] = codeformer_weight
                
                try:
                    # Make API call to the server
                    response = requests.post(f"{sd_server}/sdapi/v1/extra-single-image", json=payload)
                    
                    if response.status_code == 200:
                        r = response.json()
                        
                        # Display upscaled image
                        upscaled_image = Image.open(BytesIO(base64.b64decode(r['image'].split(",", 1)[0])))
                        
                        # Show comparison
                        st.text(f"Upscaled dimensions: {upscaled_image.width} x {upscaled_image.height} pixels")
                        st.image(upscaled_image, caption="Upscaled Image", use_column_width=True)
                        
                        # Download button
                        buf = BytesIO()
                        upscaled_image.save(buf, format="PNG")
                        byte_im = buf.getvalue()
                        st.download_button(
                            label="Download Upscaled Image",
                            data=byte_im,
                            file_name="upscaled_image.png",
                            mime="image/png",
                            key="download_upscaled"
                        )
                        
                        # Show image info
                        with st.expander("Upscaling Information"):
                            info_dict = {
                                "Original Size": f"{image.width} x {image.height} px",
                                "Upscaled Size": f"{upscaled_image.width} x {upscaled_image.height} px",
                                "Upscaler Used": selected_upscaler,
                                "Upscale Factor": upscale_factor if resize_mode == "Scale from original" else f"Custom ({target_width}x{target_height})",
                                "Face Restoration": f"{face_restorer} (Weight: {codeformer_weight})" if face_restoration else "None"
                            }
                            
                            for key, value in info_dict.items():
                                st.text(f"{key}: {value}")
                    else:
                        st.error(f"Error: {response.status_code}, {response.text}")
                except Exception as e:
                    st.error(f"Error upscaling image: {e}")
                    st.info("Make sure the server is running and the API is accessible.")
    else:
        st.info("Please upload an image to upscale.")