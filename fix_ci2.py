path = r"C:\OpenCodeProyects\ECCSAWebApps\Dashboard\.github\workflows\build-image.yml"
with open(path, "r", encoding="utf-8") as f:
    content = f.read()

old = "          build-args: |\n            BUILD_ID=${{ github.sha }}"
new = "          build-args: |\n            BUILD_ID=${{ github.sha }}\n            CACHEBUST=${{ github.run_id }}"

assert old in content, "old not found"
content = content.replace(old, new, 1)

with open(path, "w", encoding="utf-8") as f:
    f.write(content)
print("Done")
