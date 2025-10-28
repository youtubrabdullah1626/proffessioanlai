import os
import sys

# Ensure repository root is on sys.path for 'don' package imports
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
if ROOT not in sys.path:
	sys.path.insert(0, ROOT)
