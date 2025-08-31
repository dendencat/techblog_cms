import os
import sys

def testing_mode(request):
    """Add IS_TESTING variable to template context"""
    IS_TESTING = os.environ.get('TESTING') == 'True' or 'PYTEST_CURRENT_TEST' in os.environ or any(
        x.endswith('pytest') for x in sys.modules.keys()
    )
    return {'IS_TESTING': IS_TESTING}
