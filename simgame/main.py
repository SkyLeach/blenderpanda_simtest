#!/usr/bin/env python3
import sys
import os

from direct.showbase.ShowBase import ShowBase
import blenderpanda

from math import pi, sin, cos
import pprint
import logging
logger = logging.getLogger(__name__)
import traceback

from direct.showbase.ShowBase import ShowBase
from panda3d.core import Point3, PointLight, VBase4

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
        self.addHorizon(Background('skysphere', filename='skysphere.bam'))
        self.addHorizon(Background('skybox', filename='skybox_1024'))
        self.load_horizon(self.horizon)
        self.setControls()
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
