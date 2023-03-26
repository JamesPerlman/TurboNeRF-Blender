""" Constants for turbo_nerf. """

__reload_order_index__ = -10

MAIN_COLLECTION_ID = "NeRF Tools"
GLOBAL_TRANSFORM_ID = "GLOBAL_TRANSFORM"
AABB_BOX_ID = "AABB_BOX"
NERF_PROPS_ID = "NERF_PROPERTIES"

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

CAMERA_FX_ID = "camera_fx"
CAMERA_FY_ID = "camera_fy"
CAMERA_CX_ID = "camera_cx"
CAMERA_CY_ID = "camera_cy"

CAMERA_K1_ID = "distortion_k1"
CAMERA_K2_ID = "distortion_k2"
CAMERA_P1_ID = "distortion_p1"
CAMERA_P2_ID = "distortion_p2"

CAMERA_IMAGE_PATH_ID = "image_path"
CAMERA_IMAGE_WIDTH_ID = "image_width"
CAMERA_IMAGE_HEIGHT_ID = "image_height"

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
OBJ_TYPE_MASK_SHAPE = "mask_shape"
OBJ_TYPE_NERF = "tn_nerf"

# Render cameras

RENDER_CAM_TYPE_ID = "render_camera_type"

RENDER_CAM_TYPE_PERSPECTIVE = "perspective"
RENDER_CAM_TYPE_SPHERICAL_QUADRILATERAL = "spherical_quadrilateral"
RENDER_CAM_TYPE_QUADRILATERAL_HEXAHEDRON = "quadrilateral_hexahedron"

RENDER_CAM_SENSOR_WIDTH_ID = "sensor_width"
RENDER_CAM_SENSOR_HEIGHT_ID = "sensor_height"
RENDER_CAM_SENSOR_DIAGONAL_ID = "sensor_diagonal"
RENDER_CAM_IS_ACTIVE_ID = "is_active"
RENDER_CAM_NEAR_ID = "near"

RENDER_CAM_SPHERICAL_QUAD_CURVATURE_ID = "curvature"

RENDER_CAM_QUAD_HEX_FRONT_SENSOR_SIZE_ID = "front_sensor_size"
RENDER_CAM_QUAD_HEX_BACK_SENSOR_SIZE_ID = "back_sensor_size"
RENDER_CAM_QUAD_HEX_SENSOR_LENGTH_ID = "sensor_length"

# Mask Shapes

MASK_TYPE_ID = "mask_type"
MASK_TYPE_BOX = "box"
MASK_TYPE_CYLINDER = "cylinder"
MASK_TYPE_SPHERE = "sphere"

MASK_MODE_ID = "mask_mode"
MASK_MODE_ADD = "add"
MASK_MODE_SUBTRACT = "subtract"

MASK_OPACITY_ID = "mask_opacity"
MASK_FEATHER_ID = "feather"

# Specific Mask Properties

MASK_BOX_DIMS_ID = "dimensions"

MASK_CYLINDER_RADIUS_ID = "radius"
MASK_CYLINDER_HEIGHT_ID = "height"

MASK_SPHERE_RADIUS_ID = "radius"

# NeRF Properties
NERF_PATH_ID = "snapshot_path"
NERF_AABB_SIZE_ID = "aabb_size"
NERF_AABB_SIZE_LOG2_ID = "aabb_size_log2"
NERF_AABB_CENTER_ID = "aabb_center"
NERF_OPACITY_ID = "opacity"
NERF_DATASET_PATH_ID = "dataset_path"
