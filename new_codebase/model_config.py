# Model Configuration
# Central configuration for all Gemini API model references
# Update these values if you need to switch models
# Reference: https://ai.google.dev/gemini-api/docs/models/gemini

# Primary text generation model for events and actions
# Options: 'gemini-2.5-flash-lite', 'gemini-2.5-flash', 'gemini-2.0-flash-lite'
TEXT_MODEL = 'gemini-2.5-flash-lite'

# Image generation model for settlement visualizations
# Options: 'gemini-2.5-flash', 'gemini-2.0-flash-exp'
IMAGE_MODEL = 'gemini-2.5-flash'

# Timeskip model (use more powerful model for complex 500-year narratives)
# Options: 'gemini-2.5-flash-lite', 'gemini-2.5-flash', 'gemini-2.5-pro'
TIMESKIP_MODEL = 'gemini-2.5-flash-lite'

# World generation model
# Options: 'gemini-2.5-flash-lite', 'gemini-2.5-flash'
WORLD_GEN_MODEL = 'gemini-2.5-flash-lite'

# Visual generation model for portraits, crisis art, settlement evolution
# Options: 'gemini-2.5-flash-image' (recommended - fast, affordable, good quality)
VISUAL_MODEL = 'gemini-2.5-flash-image'

# API Configuration
API_VERSION = 'v1beta'  # Required for Gemini 2.x models
