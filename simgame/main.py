#!/usr/bin/env python3
import sys
import os
from math import pi, sin, cos
import pprint
import logging
logger = logging.getLogger(__name__)
import traceback

from direct.showbase.ShowBase import ShowBase
from panda3d.core import *
import blenderpanda

from simpleconsole import ConsoleWindow

load_prc_file_data("", """
    notify-level-lui info
    text-minfilter linear
    text-magfilter linear
    text-pixels-per-unit 32
    sync-video #f
    textures-power-2 none
    show-frame-rate-meter #t
    win-size 780 630
    window-title LUI Demo
    win-fixed-size #f
""")

# test panda_LUI
# -- fix LUI --from Builtin.LUISkin import LUIDefaultSkin
# -- fix LUI --from Builtin.LUIFrame import LUIFrame
# -- fix LUI --from Builtin.LUILabel import LUILabel
# -- fix LUI --from Builtin.LUIInputField import LUIInputField
# -- fix LUI --from Builtin.LUIFormattedLabel import LUIFormattedLabel
# -- fix LUI --from Builtin.LUIScrollableRegion import LUIScrollableRegion
# -- fix LUI --from Builtin.LUIObject import LUIObject
# -- fix LUI --from Builtin.LUIRegion import LUIRegion
# -- fix LUI --from Builtin.LUIInputHandler import LUIInputHandler
# -- fix LUI --from Builtin.LUIVerticalLayout import LUIVerticalLayout
# -- fix LUI --from Skins.Metro.LUIMetroSkin import LUIMetroSkin

from scene import * # SceneInfo, Scene, SceneObject
from testscene import GameTest

#local imports
#from InteractiveConsole import pandaConsole, INPUT_CONSOLE, INPUT_GUI, OUTPUT_PYTHON, OUTPUT_IRC


class SIMGame(ShowBase):

    wiresky       = False
    # The currently selected scene
    current_scene = None
    # The scene to use on startup
    start_scene   = 'gametest'
    surfdog       = None
    cannon        = None
    console       = None

    horizon       = None #current active horizon name

    registered_scenes = {}
    horizons          = {}
    loaded_obs        = {}

    def load_registered_scenes(self):
        for (name,scene) in self.registered_scenes.items():
            self.loaded_obs[name] = \
                scene.load(self.loader, self.render)
            if not self.current_scene and name == self.start_scene:
                # set current scene handle
                self.current_scene = scene
                # register game camera to scene control
                self.current_scene.register_camera(self.camera)
                # register any tasks in the scene
                self.current_scene.register_tasks(self.taskMgr)

    def load_scene(self, name=None, sceneinfo=None):
        name = name if name else sceneinfo.name
        try:
            if name in self.loaded_obs:
                return self.loaded_obs[name]
            else:
                if not sceneinfo:
                    sceneinfo = self.registered_scenes[name]
                self.loaded_obs[name] =\
                    sceneinfo.load(self.loader, self.render)
                return self.loaded_obs[name]
        except:
            logger.warn('No scene with name "%s" registered.')

    def addScene(self, scene):
        self.registered_scenes[scene.name] = scene
        return scene

    def addHorizon(self, bg):
        self.horizons[bg.name] = bg
        return bg

    def load_horizon(self, name=None, horizoninfo=None):
        if not name:
            name = horizoninfo.name
        horizon = None
        try:
            if name in self.loaded_obs:
                return self.loaded_obs[name]
            else:
                if not horizoninfo:
                    horizoninfo = self.horizons[name]
                logger.debug('Loading horizon "%s"' % (horizoninfo.name))
                logger.debug('HorizonInfo: %s' % (horizoninfo))
                horizon = horizoninfo.load(self.loader, self.render)
                # save as loaded
                self.loaded_obs[name] = horizon
                horizon = self.loaded_obs[name]
                horizon.reparentTo(self.camera)
                #horizon.setScale(0.0015, 0.0015, 0.0015)
                horizon.set_two_sided(True)
                horizon.set_bin("background", 0)
                horizon.set_depth_write(False)
                horizon.set_compass()
                # if not currently active horizon, hide it
                if self.horizon != horizoninfo.name:
                    horizon.hide()
                return horizon
        except:
            traceback.print_exc()
            logger.warn('No horizon with name "%s" registered.' % (name))

    def __init__(self):
        load_prc_file_data('', 'textures-power-2 none')
        super().__init__()
        blenderpanda.init(self)
        self.accept('escape', sys.exit)

        self.addScene(GameTest())
        self.addScene(Scene('surfdog', filename='surfdog',
            scale=[5.0, 0.1, 5.0],
            position=[-8, 22, -2]
        ))
#         self.addScene(Scene('cannon', filename='cannon',
#             position=[0,22,0],
#             hpr=[-45,0,0]
#         ))
        self.load_registered_scenes()
        # setup Horizons
        self.horizon = 'skysphere'
        self.addHorizon(Background('skysphere', filename='skysphere_mk2.egg'))
        self.addHorizon(Background('skybox', filename='skybox_1024'))
        self.load_horizon(self.horizon)
        self.setControls()

        self.console = ConsoleWindow(self)
        #big mesh test with point light
        # light
#         plight = PointLight('plight')
#         plight.setColor(VBase4(0.2, 0.2, 0.2, 1))
#         plight.setAttenuation((1, 0, 1))
# 
#         plnp = self.render.attachNewNode(plight)
#         plnp.setPos(1, 21, -20)
#         self.render.setLight(plnp)
#         # bigmesh
#         self.fusion_reactor = self.loader.loadModel("coil")
#         #self.fusion_reactor.setScale(4,4,4)
#         self.fusion_reactor.reparentTo(self.render)
# #        self.fusion_reactor.set_two_sided(True)
#         self.fusion_reactor.setPos(0, 22, -20)
#         #self.fusion_reactor.setH(-90)

# -actor-         # Load and transform the panda actor.
# -actor-         self.pandaActor = Actor("models/panda-model",
# -actor-                                 {"walk": "models/panda-walk4"})
# -actor-         self.pandaActor.setScale(0.005, 0.005, 0.005)
# -actor-         self.pandaActor.reparentTo(self.render)
# -actor-         # Loop its animation.
# -actor-         self.pandaActor.loop("walk")
# -actor- 
# -actor-         # Create the four lerp intervals needed for the panda to
# -actor-         # walk back and forth.
# -actor-         pandaPosInterval1 = self.pandaActor.posInterval(13,
# -actor-             Point3(0, -10, 0),
# -actor-             startPos=Point3(0, 10, 0))
# -actor-         pandaPosInterval2 = self.pandaActor.posInterval(13,
# -actor-             Point3(0, 10, 0),
# -actor-             startPos=Point3(0, -10, 0))
# -actor-         pandaHprInterval1 = self.pandaActor.hprInterval(3,
# -actor-             Point3(180, 0, 0),
# -actor-             startHpr=Point3(0, 0, 0))
# -actor-         pandaHprInterval2 = self.pandaActor.hprInterval(3,
# -actor-             Point3(0, 0, 0),
# -actor-             startHpr=Point3(180, 0, 0))
# -actor- 
# -actor-         # Create and play the sequence that coordinates the intervals.
# -actor-         self.pandaPace = Sequence(pandaPosInterval1,
# -actor-                                   pandaHprInterval1,
# -actor-                                   pandaPosInterval2,
# -actor-                                   pandaHprInterval2,
# -actor-                                   name="pandaPace")
# -actor-         self.pandaPace.loop()


#        self.console = pandaConsole(
#            INPUT_CONSOLE|INPUT_GUI|OUTPUT_PYTHON|OUTPUT_IRC,
#            locals()
#        )
#        self.console = pandaConsole(
#            INPUT_CONSOLE|INPUT_GUI|OUTPUT_PYTHON,
#            locals()
#        )

        # ----- LUI test code. -----
        #base.win.set_clear_color(Vec4(0.1, 0.0, 0.0, 1))
# -- fix LUI --        self.skin = LUIDefaultSkin()
# -- fix LUI --        self.skin.load()
# -- fix LUI --
# -- fix LUI --        # Initialize LUI
# -- fix LUI --        self.region = LUIRegion.make("LUI", base.win)
# -- fix LUI --        self.handler = LUIInputHandler()
# -- fix LUI --        base.mouseWatcher.attach_new_node(self.handler)
# -- fix LUI --        self.region.set_input_handler(self.handler)
# -- fix LUI --
# -- fix LUI --        # Title
# -- fix LUI --        title_label = LUILabel(parent=self.region.root,
# -- fix LUI --                text="LUI Console Example",
# -- fix LUI --                font_size=40, font="header", pos=(25, 17))
# -- fix LUI --
# -- fix LUI --        # Container
# -- fix LUI --        container = LUIFrame(parent = self.region.root, width=700, height=500,
# -- fix LUI --            style=LUIFrame.FS_sunken, margin=30, top=50)
# -- fix LUI --
# -- fix LUI --        self.text_container = LUIScrollableRegion(parent=container, width=675,
# -- fix LUI --                height=440, padding=0)
# -- fix LUI --
# -- fix LUI --        #base.win.set_clear_color(Vec4(0.1, 0.1, 0.1, 1.0))
# -- fix LUI --        self.layout = LUIVerticalLayout(parent=self.text_container.content_node)
# -- fix LUI --
# -- fix LUI --        # Create the input box
# -- fix LUI --        self.input_field = LUIInputField(parent=container, bottom=0, left=0, width="100%")
# -- fix LUI --        self.input_field.bind("enter", self.send_command)
# -- fix LUI --        self.input_field.request_focus()
# -- fix LUI --
# -- fix LUI --        # Add some initial commands
# -- fix LUI --        for demo_command in ["Hello world!",
# -- fix LUI --                "This is a simple console",
# -- fix LUI --                "You can type commands like this:",
# -- fix LUI --                "/test"]:
# -- fix LUI --            self.input_field.trigger_event("enter", demo_command)

    def send_command(self, event):
        """ Called when the user presses enter in the input field, submits the
        command and prints something on the console """
        label = LUIFormattedLabel()
        color = (0.9, 0.9, 0.9, 1.0)
        if event.message.startswith("/"):
            color = (0.35, 0.65, 0.24, 1.0)
        label.add(text=">>>  ", color=(0.35, 0.65, 0.24, 1.0))
        label.add(text=event.message, color=color)
        self.layout.add(label)

        result = LUIFormattedLabel()
        if sys.version_info[0]==3 and sys.version_info[1]>2:
            import codecs
            result.add("Your command in rot13: " + codecs.encode(event.message, "rot13"), color=(0.4, 0.4, 0.4, 1.0))
        else:
            result.add("Your command in rot13: " + event.message.encode("rot13"), color=(0.4, 0.4, 0.4, 1.0))
        self.layout.add(result)
        self.input_field.clear()

        self.text_container.scroll_to_bottom()


    def toggleConsole(self):
        #unset all controls but console
        self.ignoreAll()
        base.camLens.setFocalLength(5)
        self.console.toggleConsole()

    def setControls(self):
        for winCtrl in self.winControls:
            if winCtrl.win == self.win:
                self.winControls.remove(winCtrl)
        self.setupWindowControls()
        # swap skybox/skysphere
        self.accept("s", self.swap_horizon)
        self.accept("w", self.toggle_sky_wireframe)
        # exit game
        self.accept("escape", sys.exit)
        # load current scene controls
        for (name,control) in self.current_scene.controlmapIter():
            self.accept(control.key, control.callback, control.args)

    def toggle_sky_wireframe(self):
        """toggle_sky_wireframe
        iterate through loaded horizons and toggle wireframe on them
        """
        if self.wiresky:
            self.wiresky = False
            self.loaded_obs[self.horizon].set_render_mode_filled()
        else:
            self.wiresky = True
            self.loaded_obs[self.horizon].set_render_mode_wireframe()

    def swap_horizon(self):
        self.loaded_obs[self.horizon].hide()
        if self.horizon == 'skybox':
            self.horizon = 'skysphere'
        else:
            self.horizon = 'skybox'

        if not self.horizon in self.loaded_obs:
            self.loaded_obs[self.horizon] = self.load_horizon(self.horizon)
        else:
            self.loaded_obs[self.horizon].show()

        # set the current render mode for the sky
        if self.wiresky:
            self.loaded_obs[self.horizon].set_render_mode_wireframe()
        else:
            self.loaded_obs[self.horizon].set_render_mode_filled()
#     def toggle_console(self):
#         if self.console.is_hidden():
#             self.console.show()
#             base.silenceInput()
#         else:
#             self.console.hide()
#             base.reviveInput()

if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    game = SIMGame()
    game.run()
