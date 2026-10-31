path = r"C:\OpenCodeProyects\ECCSAWebApps\Dashboard\Dockerfile"
with open(path, "r", encoding="utf-8") as f:
    lines = f.readlines()
for i, line in enumerate(lines):
    print(f"L{i+1}: {line.rstrip()}")
