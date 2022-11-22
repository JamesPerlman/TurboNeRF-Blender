

import utility.load_ngp
import pyngp as ngp
import numpy as np
from pathlib import Path
tb = ngp.Testbed(ngp.TestbedMode.Nerf)
tb.shall_train = False
from PIL import Image
import threading

DEFAULT_NGP_SCALE = 0.33
DEFAULT_NGP_ORIGIN = np.array([0.5, 0.5, 0.5])
def nerf_matrix_to_ngp(nerf_matrix: np.matrix) -> np.matrix:
    result = np.matrix(nerf_matrix)
    result[:, 0:3] *= DEFAULT_NGP_SCALE
    result[:3, 3] = result[:3, 3] * DEFAULT_NGP_SCALE + DEFAULT_NGP_ORIGIN.reshape(3, 1)

    # Cycle axes xyz<-yzx
    result[:3, :] = np.roll(result[:3, :], -1, axis=0)

    return result
    

def output_path(i):
    return Path(f"./test/img_{i}.png")

n = 0


def callback(res):
    global n
    image = res
    n += 1
    Image.fromarray((image * 255).astype(np.uint8)).convert('RGBA').save(output_path(n).absolute())
    print(f"saved {res}")

res = np.array([200, 200])
# tb.render(1920, 1080, 1, True);
def render(use_new=True):
    global n
    print(f"RENDERING {n}")
    if use_new:
        
        ds = ngp.DownsampleInfo.MakeFromMip(res, 0)
        output = ngp.RenderOutputProperties(
            res,
            ds,
            1,
            ngp.ColorSpace.SRGB,
            ngp.TonemapCurve.Identity,
            0.0,
            np.array([0.0, 0.0, 0.0, 0.0]),
            False
        )
        camera = ngp.RenderCameraProperties(
            transform=nerf_matrix_to_ngp(np.eye(4))[:-1,:],
            model=ngp.CameraModel.Perspective,
            focal_length=1080.0,
            near_distance=0.01,
            aperture_size=0.0,
            focus_z=1.0,
            spherical_quadrilateral=ngp.SphericalQuadrilateralConfig.Zero(),
            quadrilateral_hexahedron=ngp.QuadrilateralHexahedronConfig.Zero()
        )
        modifiers = ngp.RenderModifiers(
            masks=[],
        )
        nerfs = [ngp.NerfDescriptor(
            snapshot_path_str="E:\\2022\\nerf-library\\FascinatedByFungi2022\\hydnellum-peckii-cluster\\ngp\\snapshot-10000.msgpack",
            aabb=ngp.BoundingBox(np.array([-8.0, -8.0, -8.0]), np.array([8.0, 8.0, 8.0])),
            transform=nerf_matrix_to_ngp(np.eye(4)),
            modifiers=ngp.RenderModifiers(masks=[])
        )]
        aabb = ngp.BoundingBox(np.array([-8.0, -8.0, -8.0]), np.array([8.0, 8.0, 8.0]))

        rreq = ngp.RenderRequest(
            output,
            camera,
            modifiers,
            nerfs,
            aabb
        )
           

        tb.request_nerf_render(rreq, callback)
    else:
        tb.set_nerf_camera_matrix(np.eye(4)[:-1,:])
        tb.load_snapshot("E:\\2022\\nerf-library\\FascinatedByFungi2022\\hydnellum-peckii-cluster\\ngp\\snapshot-10000.msgpack")
        result = tb.render(res[0], res[1], 1, True)
        callback(result)
        

render(True)
# for i in range(28):
#    threading.Timer(1 * i, render, [True]).start()
