
def get_camera_focal_length(camera, scene):
    cam_data = camera.data

    render_scale = scene.render.resolution_percentage / 100.0
    ngp_w = scene.render.resolution_x * render_scale
    ngp_h = scene.render.resolution_y * render_scale

    # get blender focal len
    bl_sw = cam_data.sensor_width
    bl_sh = cam_data.sensor_height
    bl_f  = cam_data.lens

    # get blender sensor size in pixels
    px_w: float

    if cam_data.sensor_fit == 'AUTO':
        bl_asp = 1.0
        ngp_asp = ngp_h / ngp_w

        if ngp_asp > bl_asp:
            px_w = ngp_h / bl_asp
        else:
            px_w = ngp_w

    elif cam_data.sensor_fit == 'HORIZONTAL':
        px_w = ngp_w

    elif cam_data.sensor_fit == 'VERTICAL':
        px_w = ngp_h * bl_sw / bl_sh
    
    # focal length in pixels
    return bl_f / bl_sw * px_w

