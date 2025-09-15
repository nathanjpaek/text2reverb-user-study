import streamlit as st
import os
import json
import random
from pathlib import Path
from datetime import datetime

# Initialize session state
if 'current_sample_idx' not in st.session_state:
    st.session_state.current_sample_idx = 0
if 'sample_order' not in st.session_state:
    st.session_state.sample_order = []
if 'ratings' not in st.session_state:
    st.session_state.ratings = {}
if 'samples' not in st.session_state:
    st.session_state.samples = None  # Will be initialized after function definitions

# Configuration
SAMPLES_DIR = "evaluation_samples"
RESULTS_DIR = "evaluation_results"
os.makedirs(RESULTS_DIR, exist_ok=True)

# Sample categories following Image2Reverb
SCENE_CATEGORIES = ["small", "medium", "large", "outdoor"]
SAMPLES_PER_CATEGORY = 2  # Following Image2Reverb's 8 total samples

# CSS for better audio player and UI
st.markdown("""
    <style>
    .stAudio > audio {
        width: 100%;
        height: 60px;
    }
    .rating-box {
        background-color: #f0f2f6;
        padding: 20px;
        border-radius: 10px;
        margin: 10px 0;
    }
    .text-prompt {
        background-color: #000000;
        padding: 15px;
        border-radius: 8px;
        margin: 15px 0;
        font-size: 1.1em;
        border-left: 4px solid #1e88e5;
    }
    </style>
""", unsafe_allow_html=True)

def load_evaluation_samples():
    """Load all evaluation samples from directory structure"""
    samples = []
    
    # Expected structure:
    # evaluation_samples/
    #   category_name/
    #     sample_id/
    #       text_prompt.txt
    #       anechoic.wav
    #       generated_reverb.wav
    #       ground_truth_reverb.wav (for comparison if available)
    
    # Check if samples directory exists
    if not os.path.exists(SAMPLES_DIR):
        st.error(f"Evaluation samples directory not found: {SAMPLES_DIR}")
        return []
    
    # Scan directory structure for real samples
    for category in os.listdir(SAMPLES_DIR):
        category_path = os.path.join(SAMPLES_DIR, category)
        if not os.path.isdir(category_path):
            continue
            
        for sample_dir in os.listdir(category_path):
            sample_path = os.path.join(category_path, sample_dir)
            if not os.path.isdir(sample_path):
                continue
                
            # Check for required files
            anechoic_path = os.path.join(sample_path, "anechoic.wav")
            generated_path = os.path.join(sample_path, "generated_reverb.wav")
            ground_truth_path = os.path.join(sample_path, "ground_truth_reverb.wav")
            text_prompt_path = os.path.join(sample_path, "text_prompt.txt")
            
            # Load text prompt if available
            if os.path.exists(text_prompt_path):
                with open(text_prompt_path, 'r') as f:
                    text_prompt = f.read().strip()
            else:
                # Use demo prompt as fallback
                sample_num = int(sample_dir.split('_')[-1]) if '_' in sample_dir else 0
                text_prompt = get_demo_text_prompt(category, sample_num)
            
            # Add sample for generated reverb if exists
            if os.path.exists(anechoic_path) and os.path.exists(generated_path):
                samples.append({
                    'id': f"{category}_{sample_dir}_generated",
                    'category': category,
                    'condition': 'generated',
                    'sample_dir': sample_dir,
                    'text_prompt': text_prompt,
                    'anechoic_path': anechoic_path,
                    'reverb_path': generated_path
                })
            
            # Add sample for ground truth reverb if exists
            if os.path.exists(anechoic_path) and os.path.exists(ground_truth_path):
                samples.append({
                    'id': f"{category}_{sample_dir}_ground_truth",
                    'category': category,
                    'condition': 'ground_truth',
                    'sample_dir': sample_dir,
                    'text_prompt': text_prompt,
                    'anechoic_path': anechoic_path,
                    'reverb_path': ground_truth_path
                })
    
    if not samples:
        st.warning("No evaluation samples found in the directory structure.")
    
    return samples

def get_demo_text_prompt(category, sample_num):
    """Generate demo text prompts based on category"""
    prompts = {
        'small': [
            "A small tiled bathroom with hard surfaces and minimal absorption",
            "A compact bedroom with carpet flooring and soft furnishings"
        ],
        'medium': [
            "A medium-sized classroom with concrete walls and large windows",
            "A living room with wooden floors and moderate furnishing"
        ],
        'large': [
            "A large cathedral with stone walls and high vaulted ceilings",
            "A spacious concert hall with acoustic treatment panels"
        ],
        'outdoor': [
            "An open field with no nearby reflective surfaces",
            "A desert landscape with distant rock formations"
        ]
    }
    
    # Handle categories not in prompts or sample_num out of range
    if category not in prompts:
        return f"A {category} space"
    
    prompt_list = prompts[category]
    if sample_num >= len(prompt_list):
        return prompt_list[0]  # Default to first prompt if index out of range
    
    return prompt_list[sample_num]

def evaluation_interface():
    """Main evaluation interface following Image2Reverb methodology"""
    samples = st.session_state.samples
    sample_order = st.session_state.sample_order
    current_idx = st.session_state.current_sample_idx
    
    if current_idx >= len(sample_order):
        show_completion()
        return
    
    # Get current sample
    sample = samples[sample_order[current_idx]]

    st.markdown("---")
    
    # Display text prompt prominently
    st.markdown("### Text Description:")
    st.markdown(
        f'<div class="text-prompt">{sample["text_prompt"]}</div>',
        unsafe_allow_html=True
    )
    
    # Audio players
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**Anechoic (Dry) Audio:**")
        anechoic_path = sample['anechoic_path']
        if os.path.exists(anechoic_path):
            st.audio(anechoic_path, format="audio/wav")
        else:
            st.warning(f"Anechoic audio file not found: {anechoic_path}")
    
    with col2:
        st.markdown("**With Reverb Applied:**")
        reverb_path = sample['reverb_path']
        if os.path.exists(reverb_path):
            st.audio(reverb_path, format="audio/wav")
        else:
            st.warning(f"Reverb audio file not found: {reverb_path}")
    
    # Rating scales (following Image2Reverb's approach)
    st.markdown("---")
    st.markdown("### Please rate the following aspects (rating scale below):")
    st.markdown("""
        - 1 = Very Poor/No Match
        - 2 = Poor
        - 3 = Acceptable
        - 4 = Good
        - 5 = Excellent""")
    
    # Load previous ratings if they exist
    existing_rating = st.session_state.ratings.get(sample['id'], {})
    
    # Define keys for this sample's widgets
    quality_key = f"quality_{sample['id']}"
    match_key = f"match_{sample['id']}"
    
    # Quality rating
    quality_rating = st.slider(
        "**1. Reverb Quality** - How would you rate the overall quality of the reverberation?",
        min_value=1,
        max_value=5,
        value=existing_rating.get('quality', 3),
        key=quality_key,
        help="1 = Very Poor, 2 = Poor, 3 = Acceptable, 4 = Good, 5 = Excellent"
    )
    
    # Match rating (key metric from Image2Reverb)
    match_rating = st.slider(
        "**2. Text-Audio Match** - How well does the reverb match what you would expect from the text description?",
        min_value=1,
        max_value=5,
        value=existing_rating.get('match', 3),
        key=match_key,
        help="1 = No match, 2 = Poor match, 3 = Moderate match, 4 = Good match, 5 = Excellent match"
    )
    
    
    # Add some spacing before buttons
    st.markdown("---")
    
    # Navigation buttons
    if current_idx > 0:
        # If not first sample, show both buttons
        col1, col2, col3, col4, col5 = st.columns([1, 1, 1, 1, 1])
        
        # Previous button
        with col1:
            if st.button("← Previous", key=f"prev_{current_idx}", type="primary", use_container_width=True):
                # Save current ratings before moving
                st.session_state.ratings[sample['id']] = {
                    'sample_id': sample['id'],
                    'category': sample['category'],
                    'condition': sample['condition'],
                    'quality': st.session_state[quality_key],
                    'match': st.session_state[match_key],
                    'order_presented': current_idx
                }
                st.session_state.current_sample_idx -= 1
                st.rerun()
        
        # Next/Submit button aligned right
        with col5:
            is_last_sample = current_idx == len(sample_order) - 1
            button_text = "Submit" if is_last_sample else "Next →"
            
            if st.button(button_text, key=f"next_{current_idx}", type="primary", use_container_width=True):
                # Save ratings
                st.session_state.ratings[sample['id']] = {
                    'sample_id': sample['id'],
                    'category': sample['category'],
                    'condition': sample['condition'],
                    'quality': st.session_state[quality_key],
                    'match': st.session_state[match_key],
                    'order_presented': current_idx
                }
                
                # Move to next sample
                st.session_state.current_sample_idx += 1
                st.rerun()
    else:
        # If first sample, only show Next button aligned right
        col1, col2, col3, col4, col5 = st.columns([1, 1, 1, 1, 1])
        
        with col5:
            is_last_sample = current_idx == len(sample_order) - 1
            button_text = "Submit" if is_last_sample else "Next →"
            
            if st.button(button_text, key=f"next_{current_idx}", type="primary", use_container_width=True):
                # Save ratings
                st.session_state.ratings[sample['id']] = {
                    'sample_id': sample['id'],
                    'category': sample['category'],
                    'condition': sample['condition'],
                    'quality': st.session_state[quality_key],
                    'match': st.session_state[match_key],
                    'order_presented': current_idx
                }
                
                # Move to next sample
                st.session_state.current_sample_idx += 1
                st.rerun()

def show_completion():
    """Show completion screen and save results"""
    st.balloons()
    st.success("🎉 Evaluation Complete! Thank you for your participation.")
    
    # Save results
    results = {
        'ratings': st.session_state.ratings,
        'completion_time': datetime.now().isoformat()
    }
    
    # Save to JSON file
    filename = f"{RESULTS_DIR}/evaluation_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(filename, 'w') as f:
        json.dump(results, f, indent=2)
    
    st.info(f"Your responses have been saved. Reference ID: {Path(filename).stem}")

# Main app flow
def main():
    st.title("🎵 Text-to-Reverb Subjective Evaluation")
    st.markdown("""
    ### Instructions:
    1. **Listen carefully** to both audio samples
    2. **Read the text description** thoroughly
    3. **Rate** based on:
       - Overall reverb quality
       - How well the reverb matches the text description
    """)
    
    # Initialize samples if not already done
    if st.session_state.samples is None:
        samples = load_evaluation_samples()
        st.session_state.sample_order = random.sample(range(len(samples)), len(samples))
        st.session_state.samples = samples
    
    # Start evaluation directly
    evaluation_interface()
    
    #with st.sidebar:
    #    st.markdown("## Instructions")
    #    st.markdown("""
    #    1. **Listen carefully** to both audio samples
    #    2. **Read the text description** thoroughly
    #    3. **Rate** based on:
    #       - Overall reverb quality
    #       - How well the reverb matches the text description
    #    4. **Optional**: Provide detailed feedback
    #    
    #    ### Rating Scale:
    #    - 1 = Very Poor/No Match
    #    - 2 = Poor
    #    - 3 = Acceptable
    #    - 4 = Good
    #    - 5 = Excellent
        
    #    ### Tips:
    #    - Use headphones for best results
    #    - Take breaks if needed
    #    - Trust your first impression
    #    """)
        
    # Show progress in sidebar
    with st.sidebar:
        if 'sample_order' in st.session_state and len(st.session_state.sample_order) > 0:
            st.markdown("---")
            st.markdown(f"**Progress:** {st.session_state.current_sample_idx}/{len(st.session_state.sample_order)}")

if __name__ == "__main__":
    main()