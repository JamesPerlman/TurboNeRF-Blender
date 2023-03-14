import bpy
import textwrap

# Thank you https://b3d.interplanety.org/en/multiline-text-in-blender-interface-panels/

def add_multiline_label(context: bpy.types.Context, text: str, parent: bpy.types.UILayout):
    chars = int(context.region.width / 12)   # 7 pix on 1 character
    wrapper = textwrap.TextWrapper(width=chars)
    text_lines = wrapper.wrap(text=text)
    for text_line in text_lines:
        parent.label(text=text_line)
