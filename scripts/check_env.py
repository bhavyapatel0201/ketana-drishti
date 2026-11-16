from dotenv import dotenv_values

v = dotenv_values(".env").get("ANTHROPIC_API_KEY") or ""
print("length:", len(v))
print("starts with:", v[:7])
print("has space or quote:", any(c in v for c in " \"'"))
print("has newline or tab:", any(c in v for c in "\r\n\t"))