## Intro
Hello, fellow NeRF enthusaist! I'm James. I made a tool for generating a `transforms.json` from a Blender project.  It's yours to use for free!

## Prerequisites
Before we begin, you'll need to get yourself set up with the following:

* [Blender Photogrammetry Importer](https://github.com/SBCV/Blender-Addon-Photogrammetry-Importer)
* A compatible NeRF renderer
  * [instant-ngp](https://github.com/NVlabs/instant-ngp) is the most popular and well supported.
  * 🚧 [TensoRF](https://github.com/JamesPerlman/TensoRF) coming soon! 
* Optional - my custom [render_nerf.py script](https://raw.githubusercontent.com/JamesPerlman/instant-ngp/custom-nerf-render/scripts/render_nerf.py) for instant-ngp
  * Just drop this into your `scripts` folder, run `python render_nerf.py --help` for details on how to use this script.
  * The script supports Multi-GPU rendering (naively). More useful scripts coming soon in an easy-to-use package.

## Tutorial

### 0. Installation
When you download this addon, it will automatically be named something like `blender_nerf_tools-master` - you will need to rename this to `instant_ngp_tools` before moving it to your addons folder.  Will fix this soon!

### 1. Set up your NeRF scene

If you're using instant-ngp to render your scenes, you'll want to use the `--keep_colmap_coords` flag when running the `colmap2nerf.py` script.

After installing this plugin and the Blender Photogrammetry Importer, go to `File > Import > Colmap (model/workspace)`

### 2. Import your COLMAP point cloud into Blender

Select the `colmap_sparse/0` folder in the importer.

In the importer settings, I recommend making the following changes:
* Disable `Import Cameras`
* Disable `Add Camera Motion as Animation`
* Enable `Suppress Distortion Warnings`

<img width="593" alt="image" src="https://user-images.githubusercontent.com/3280839/182312215-38d81cfb-64d5-46df-a9b5-e43b8ac4d3c0.png">

### 3. Adjust the scene, set up NeRF tools

Your scene will most likely look a bit wonky at this point.  That's the way it is right now, unfortunately.  I'm working on a way to get around that.  For now you'll have to align the scene manually.

In Object Mode, activate the 3D View side panel (hotkey: `N`) 

Find the InstantNGP_NeRF panel and press `Set up Instant-NGP Scene`.

<img width="263" alt="image" src="https://user-images.githubusercontent.com/3280839/182314943-463c7387-876c-4d5c-80b3-8816ef1a2cdf.png">

This should give you a few new objects, among them one is called `GLOBAL_TRANSFORM`.

Do not rename any of these objects.  To reorient the scene, all you need to do is find your `OpenGL Point Cloud` object from the COLMAP import step, and add to it a `Copy Transforms` constraint where the target is `GLOBAL_TRANSFORM`.

Now, adjust `GLOBAL_TRANSFORM` until the scene is aligned to your liking.

### 4. Animate a blender camera

Make sure the camera you want to export is set in your Scene settings
<img width="217" alt="image" src="https://user-images.githubusercontent.com/3280839/182314076-715d39b9-388b-470c-9260-3901e9888df6.png">

Animatable properties include:
* Camera transform + rotation (Compatible with instant-ngp render script)
* Camera focal length / field of view (Only compatible with my render script)
* AABB Cropping (Only compatible with my render script)
* 🚧 Depth of Field (Coming soon!)

Unsupported properties include:
* GLOBAL_TRANSFORM location/rotation/scale

### 5. Exporting transforms.json

Any changes made to the `Format` and `Frame Range` properties (in the `Scene` panel) will reflect in the final render, with the exception of `Frame Rate` which needs to be set via the render script.

<img width="216" alt="image" src="https://user-images.githubusercontent.com/3280839/182316140-42b91ef7-72b5-4605-9b46-a41589e6d555.png">

It is important to set the `Frame Start` and `End`, this dictates which frames will show up in the final json file.

Once your scene is ready, simply go to `File > Export > Instant-NGP Transforms for Rendering` and save your `render.json` (a modified `transforms.json`)

### 6. Rendering

You will need to train a checkpoint first in order to pass to the render script.

If you use my [custom render_nerf.py script](https://raw.githubusercontent.com/JamesPerlman/instant-ngp/custom-nerf-render/scripts/render_nerf.py), simply pass the `render.json` into the `--frames_json` argument

### 7. Enjoy!

If you found this useful and make something cool, please feel free to tag me on social media.

Twitter: [@jperldev](https://twitter.com/jperldev)
Instagram: [@jperl](https://instagram.com/jperl)
