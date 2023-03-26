import bpy
import collections.abc

# dirty hack - re-evaluates drivers (thank you https://developer.blender.org/T74000)

def force_update_drivers(obj):
    obj.hide_render = obj.hide_render

# lock a driver to a value (todo: handle string values)
def lock_prop_with_driver(obj, prop_name, value):
    fcs = obj.driver_add(prop_name)

    if not isinstance(fcs, collections.abc.Iterable):
        fcs = [fcs]

    drivers = [fc.driver for fc in fcs]
    if isinstance(value, collections.abc.Iterable):
        for i, driver in enumerate(drivers):
            driver.expression = f"{value[i]}"
    else:
        for driver in drivers:
            driver.expression = f"{value}"
