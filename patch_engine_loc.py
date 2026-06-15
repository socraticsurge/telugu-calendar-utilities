import re
with open('telugu_panchangam/engines/base.py', 'r') as f:
    content = f.read()

content = content.replace("class Location(BaseModel):", "class Location(BaseModel):\n    model_config = {\"frozen\": True}")

with open('telugu_panchangam/engines/base.py', 'w') as f:
    f.write(content)
