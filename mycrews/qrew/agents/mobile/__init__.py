from .android import android_api_client_agent, android_storage_agent, android_ui_agent
from .ios import ios_api_client_agent, ios_storage_agent, ios_ui_agent

# You might want to make them available directly, or nested.
# For direct availability:
__all__ = [
    'android_api_client_agent',
    'android_storage_agent',
    'android_ui_agent',
    'ios_api_client_agent',
    'ios_storage_agent',
    'ios_ui_agent'
]
# Alternatively, to keep them nested under android and ios:
# from . import android
# from . import ios
# __all__ = ['android', 'ios']
# Let's go with direct availability for easier access by crews if they need specific platform agents.
