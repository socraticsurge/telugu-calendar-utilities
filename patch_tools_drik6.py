with open('telugu_panchangam/mcp/tools.py', 'r') as f:
    content = f.read()

# Make the cache more robust and make sure we don't accidentally run into the location hash issue
import re
with open('telugu_panchangam/mcp/tools.py', 'w') as f:
    f.write(content)
