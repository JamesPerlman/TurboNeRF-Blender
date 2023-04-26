import mathutils

# No idea why we need this, but if we don't adjust nerfs they are completely off axis
NERF_ADJUSTMENT_MATRIX = mathutils.Matrix(
    (
        (0.0, 0.0, -1.0, 0.0),
        (1.0, 0.0, 0.0, 0.0),
        (0.0, -1.0, 0.0, 0.0),
        (0.0, 0.0, 0.0, 1.0)
    )
)
