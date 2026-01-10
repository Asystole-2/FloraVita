import os
import sys

print(f"Python executable: {sys.executable}")
print(f"Python version: {sys.version}")
print(f"Current directory: {os.getcwd()}")

# Test authlib import
try:
    import authlib
    print(f"✓ Authlib version: {authlib.__version__}")

    # Check what's in integrations
    import authlib.integrations
    print("✓ authlib.integrations imported")

    # List available modules
    import pkgutil
    path = authlib.integrations.__path__
    print(f"Integration modules available:")
    for finder, name, ispkg in pkgutil.iter_modules(path):
        print(f"  - {name}")

    # Try specific import
    try:
        from authlib.integrations.flask_client import OAuth
        print("✓ SUCCESS: from authlib.integrations.flask_client import OAuth")
    except ImportError as e:
        print(f"✗ FAILED flask_client import: {e}")

        # Try different import style
        try:
            import authlib.integrations.flask_client as fc
            print(f"✓ SUCCESS with import authlib.integrations.flask_client")
            print(f"  Available in module: {dir(fc)}")
        except ImportError as e2:
            print(f"✗ Also failed: {e2}")

except ImportError as e:
    print(f"✗ Failed to import authlib at all: {e}")