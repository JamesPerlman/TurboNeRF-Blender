import glob
import os
import sys
NGP_DIR = "C:\\Users\\bizon\\Developer\\blender-ngp"

pyd_dirs = []
pyd_dirs += [os.path.dirname(pyd) for pyd in glob.iglob(os.path.join(NGP_DIR, "build*", "**/*.pyd"), recursive=True)]
pyd_dirs += [os.path.dirname(pyd) for pyd in glob.iglob(os.path.join(NGP_DIR, "build*", "**/*.so"), recursive=True)]
pyd_dirs += [os.path.dirname(pyd) for pyd in glob.iglob(os.path.join(NGP_DIR, "out/build/x64-Debug*", "**/*.pyd"), recursive=True)]
pyd_dirs += [os.path.dirname(pyd) for pyd in glob.iglob(os.path.join(NGP_DIR, "out/build/x64-Debug*", "**/*.so"), recursive=True)]

for pyd_dir in pyd_dirs:
    if not pyd_dir in sys.path:
        sys.path.append(pyd_dir)
