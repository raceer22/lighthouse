from blender_runner import run_in_blender

# A local light "Key" in a local collection "Lights", next to a linked "Key" in a linked "Lights".
SAME_NAMES = """
        import os, tempfile
        import lighthouse
        lighthouse.register()
        empty_scene()
        for collection in list(bpy.data.collections):
            bpy.data.collections.remove(collection)
        library = os.path.join(tempfile.mkdtemp(), "library.blend")
        lights = bpy.data.collections.new("Lights")
        key = bpy.data.objects.new("Key", bpy.data.lights.new("Key", "POINT"))
        lights.objects.link(key)
        bpy.data.libraries.write(library, {lights})
        bpy.context.scene.collection.children.link(lights)
        with bpy.data.libraries.load(library, link=True) as (source, target):
            target.collections = ["Lights"]
        bpy.context.scene.collection.children.link(target.collections[0])
        bpy.context.view_layer.update()
        local = {"object": key, "collection": lights}
        linked = {"object": target.collections[0].objects[0], "collection": target.collections[0]}
        path = target.collections[0].library.filepath

        def hidden(id):
            return [id.hide_render, id.hide_viewport]

        def states():
            return {
                "local": hidden(local["object"]), "linked": hidden(linked["object"]),
                "local group": hidden(local["collection"]), "linked group": hidden(linked["collection"]),
            }
"""

SHOWN = [False, False]
HIDDEN = [True, True]


def test_mute_light_changes_only_the_light_from_its_library():
    result = run_in_blender(SAME_NAMES + """
        bpy.ops.lighthouse.mute_light(name="Key", library="")
        after_local = states()
        bpy.ops.lighthouse.mute_light(name="Key", library="")
        bpy.ops.lighthouse.mute_light(name="Key", library=path)
        report({"local": after_local, "linked": states()})
    """)

    assert result["local"]["local"] == HIDDEN and result["local"]["linked"] == SHOWN
    assert result["linked"]["local"] == SHOWN and result["linked"]["linked"] == HIDDEN


def test_solo_light_hides_the_same_named_light_from_the_other_library():
    result = run_in_blender(SAME_NAMES + """
        bpy.ops.lighthouse.solo_light(name="Key", library="")
        after_local = states()
        bpy.ops.lighthouse.solo_light(name="Key", library="")
        bpy.ops.lighthouse.solo_light(name="Key", library=path)
        report({"local": after_local, "linked": states()})
    """)

    assert result["local"]["local"] == SHOWN and result["local"]["linked"] == HIDDEN
    assert result["linked"]["local"] == HIDDEN and result["linked"]["linked"] == SHOWN


def test_select_light_selects_only_the_light_from_its_library():
    result = run_in_blender(SAME_NAMES + """
        def selected():
            return {"local": local["object"].select_get(), "linked": linked["object"].select_get(),
                    "active is linked": bpy.context.view_layer.objects.active == linked["object"]}
        bpy.ops.lighthouse.select_light(name="Key", library="")
        after_local = selected()
        bpy.ops.lighthouse.select_light(name="Key", library=path)
        report({"local": after_local, "linked": selected()})
    """)

    assert result == {
        "local": {"local": True, "linked": False, "active is linked": False},
        "linked": {"local": False, "linked": True, "active is linked": True},
    }


def test_hide_group_changes_only_the_collection_from_its_library():
    result = run_in_blender(SAME_NAMES + """
        bpy.ops.lighthouse.hide_group(name="Lights", library="")
        after_local = states()
        bpy.ops.lighthouse.hide_group(name="Lights", library="")
        bpy.ops.lighthouse.hide_group(name="Lights", library=path)
        report({"local": after_local, "linked": states()})
    """)

    assert result["local"]["local group"] == HIDDEN and result["local"]["linked group"] == SHOWN
    assert result["linked"]["local group"] == SHOWN and result["linked"]["linked group"] == HIDDEN


def test_select_group_selects_only_the_lights_of_the_collection_from_its_library():
    result = run_in_blender(SAME_NAMES + """
        def selected():
            return {"local": local["object"].select_get(), "linked": linked["object"].select_get()}
        bpy.ops.lighthouse.select_group(name="Lights", library="")
        after_local = selected()
        bpy.ops.lighthouse.select_group(name="Lights", library=path)
        report({"local": after_local, "linked": selected()})
    """)

    assert result == {
        "local": {"local": True, "linked": False},
        "linked": {"local": False, "linked": True},
    }


def test_find_object_ignores_a_matching_object_outside_the_view_layer():
    result = run_in_blender("""
        from lighthouse.lights import find_object
        empty_scene()
        inside = add_light("Inside")
        outside = bpy.data.objects.new("Outside", bpy.data.lights.new("Outside", "POINT"))
        layer = bpy.context.view_layer
        report({"inside": find_object(layer, "Inside", "") == inside,
                "outside": find_object(layer, "Outside", "")})
    """)

    assert result == {"inside": True, "outside": None}
