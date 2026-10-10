import textwrap

from blender_runner import run_installed


def test_installed_add_on_has_a_preferences_panel(tmp_path):
    prefs = run_installed("""
        addon = bpy.context.preferences.addons["bl_ext.user_default.lighthouse"]
        report([addon.preferences is not None, hasattr(type(addon.preferences), "draw")])
    """, tmp_path / "config")[0]

    assert prefs == [True, True]


# A stand-in for bpy's UILayout that records what draw() puts on it.
RECORDER = """
class Recorder:
    def __init__(self, log):
        self.log = log
    def row(self, **kwargs):
        return Recorder(self.log)
    column = box = row
    def operator(self, idname, text="", **kwargs):
        self.log.append(["operator", idname, text])
        return type("Props", (), {})()
    def label(self, text="", **kwargs):
        self.log.append(["label", text])
    def prop(self, data, name, **kwargs):
        self.log.append(["prop", name])

def drawn(cls):
    log = []
    holder = type("Holder", (), {"layout": Recorder(log)})()
    cls.draw(holder, bpy.context)
    return log
"""


def test_preferences_offer_restore_with_a_hint(tmp_path):
    log = run_installed(RECORDER + textwrap.dedent("""
        addon = bpy.context.preferences.addons["bl_ext.user_default.lighthouse"]
        report(drawn(type(addon.preferences)))
    """), tmp_path / "config")[0]

    assert ["operator", "lighthouse.restore_default_presets", "Restore Default Presets"] in log
    assert ["label", "Brings back deleted defaults. Defaults you edited are kept."] in log


def test_presets_panel_offers_save_and_delete_but_not_restore(tmp_path):
    log = run_installed(RECORDER + textwrap.dedent("""
        bpy.context.window_manager.lighthouse.preset = "USER:Candle"
        report(drawn(bpy.types.LIGHTHOUSE_PT_presets))
    """), tmp_path / "config")[0]

    buttons = [entry[2] for entry in log if entry[0] == "operator"]
    assert buttons == ["Apply", "Save", "Delete"]
