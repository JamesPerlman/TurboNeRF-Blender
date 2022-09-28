""" Constants for blender_nerf_tools. """

__reload_order_index__ = -10

MAIN_COLLECTION_ID = "NeRF Tools"
GLOBAL_TRANSFORM_ID = "GLOBAL_TRANSFORM"
AABB_BOX_ID = "AABB_BOX"
NERF_PROPS_ID = "NERF_PROPERTIES"

# TODO: Come up with a way to present NGP coords instead of Blender/NeRF coords
AABB_SIZE_ID = "aabb_size"
AABB_SIZE_DEFAULT = 16 / 0.33

AABB_MIN_ID = "aabb_min_2"
AABB_MIN_DEFAULT = (-AABB_SIZE_DEFAULT / 2, -AABB_SIZE_DEFAULT / 2, -AABB_SIZE_DEFAULT / 2)

AABB_MAX_ID = "aabb_max_2"
AABB_MAX_DEFAULT = (AABB_SIZE_DEFAULT / 2, AABB_SIZE_DEFAULT / 2, AABB_SIZE_DEFAULT / 2)

AABB_IS_CUBE_ID = "is_aabb_cube"
AABB_IS_CUBE_DEFAULT = False

TRAINING_STEPS_ID = "training_steps"
TRAINING_STEPS_DEFAULT = 10000

TIME_ID = "time"
TIME_DEFAULT = 0.0

# Camera property identifiers
CAMERA_NEAR_ID = "camera_near"
CAMERA_NEAR_DEFAULT = 1.0

CAMERA_FAR_ID = "camera_far"
CAMERA_FAR_DEFAULT = 8.0

CAMERA_USE_FOR_TRAINING_ID = "use_for_training"
CAMERA_USE_FOR_TRAINING_DEFAULT = True

CAMERA_K1_ID = "distortion_k1"
CAMERA_K2_ID = "distortion_k2"
CAMERA_P1_ID = "distortion_p1"
CAMERA_P2_ID = "distortion_p2"

CAMERA_IMAGE_PATH_ID = "image_path"

# Point cloud
POINT_CLOUD_NAME_DEFAULT = "Point Cloud Scene Representation"

POINT_CLOUD_POINT_SIZE_ID = "point_size"
POINT_CLOUD_POINT_SIZE_DEFAULT = 1.0

# Object type identifiers
OBJ_TYPE_ID = "object_type"

OBJ_TYPE_TRAIN_CAMERA = "train_camera"
OBJ_TYPE_RENDER_CAMERA = "render_camera"
OBJ_TYPE_IMG_PLANE = "image_plane"
OBJ_TYPE_POINT_CLOUD = "point_cloud"
