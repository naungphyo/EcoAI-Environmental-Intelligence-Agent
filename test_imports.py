print("Testing imports...")

try:
    import dotenv
    print("✓ dotenv")
except Exception as e:
    print(f"✗ dotenv MISSING: {e}")

try:
    import requests
    print("✓ requests")
except Exception as e:
    print(f"✗ requests MISSING: {e}")

try:
    from bs4 import BeautifulSoup
    print("✓ beautifulsoup4")
except Exception as e:
    print(f"✗ beautifulsoup4 MISSING: {e}")

try:
    import langchain
    print("✓ langchain")
except Exception as e:
    print(f"✗ langchain MISSING: {e}")

try:
    from langchain.tools import tool
    print("✓ langchain.tools")
except Exception as e:
    print(f"✗ langchain.tools MISSING: {e}")

try:
    from langgraph.graph import StateGraph
    print("✓ langgraph")
except Exception as e:
    print(f"✗ langgraph MISSING: {e}")

print("\n=== If all show ✓, packages are installed! ===")
