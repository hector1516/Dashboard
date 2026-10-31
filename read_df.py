path = r"C:\OpenCodeProyects\ECCSAWebApps\Dashboard\Dockerfile"
with open(path, "r", encoding="utf-8") as f:
    lines = f.readlines()
with open(r"C:\OpenCodeProyects\ECCSAWebApps\Dashboard\dockerfile_content.txt", "w", encoding="utf-8") as f:
    for i, line in enumerate(lines):
        f.write(f"L{i+1}: {line}")
print("Done")
