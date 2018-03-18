#!/usr/bin/env python3
import sys
import os
from math import pi, sin, cos
import pprint
import logging
logger = logging.getLogger(__name__)
import traceback
from optparse import OptionParser

from direct.showbase.ShowBase import ShowBase
from panda3d.core import *
import blenderpanda

from simpleconsole import ConsoleWindow
from version import VersionInfo
    #want-directtools true
    #want-tk true

load_prc_file_data("", """
    notify-level-lui info
    text-minfilter linear
    text-magfilter linear
    text-pixels-per-unit 32
    sync-video #f
    textures-power-2 none
    show-frame-rate-meter #t
    win-size 1920 1080
    window-title S.I.M.
    win-fixed-size #f
    framebuffer-multisample 1
    multisamples 8
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

#from scene import * # SceneInfo, Scene, SceneObject
import scenes
from scenes.scene import Background

#local imports
#from InteractiveConsole import pandaConsole, INPUT_CONSOLE, INPUT_GUI, OUTPUT_PYTHON, OUTPUT_IRC


class SIMGame(ShowBase):

    wiresky       = False
    # The currently selected scene
    current_scene = None
    # The scene to use on startup
    start_scene   = 'corvette'
# - surfdog -     surfdog       = None
# -cannon-     cannon        = None
    console       = None

    horizon       = None #current active horizon name

    registered_scenes = {}
    horizons          = {}
    loaded_obs        = {}
    cvMgr             = None
    _dt_enabled       = False
    _dttk_enabled     = False

    @property
    def version(self):
        return 

    def load_registered_scenes(self):
        for (name,scene) in self.registered_scenes.items():
            self.load_scene(sceneinfo=scene)
            #self.loaded_obs[name] = \
            #    scene.load(self.loader, self.render)
            #for part in self.loaded_obs[name].:
            #    logger.debug('Scene obj {} loaded...'.format(part))
            if not self.current_scene and name == self.start_scene:
                # set current scene handle
                self.current_scene = scene
                # register game camera to scene control
                self.current_scene.register_camera(self.camera)
                # register any tasks in the scene
                self.current_scene.register_tasks(self.taskMgr)
                #logger.debug(pprint.pformat(dir(self.loaded_obs[name])))
            else:
                self.loaded_obs[name].hide()
                #scene.hide()
            #this is redundant?
            #self.loaded_obs[name].wrtReparentTo(self.render)
            #hand off the nodetree to the scene so it can set itself up
            scene.setup(self.loaded_obs[name])

    def set_scene(self, name=None, sceneinfo=None, scene=None):
        if not scene:
            try:
                self.load_scene(name=name, sceneinfo=sceneinfo)
            except:
                logger.warn('set_scene: nothing to work on')
                return False
        self.current_scene.hide()
        self.current_scene = scene
        self.current_scene.show()
        self.setControls()
        return True

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
                if logger.isEnabledFor(logging.DEBUG):
                    logger.debug('Scenegraph:')
                    logger.debug('    {}'.format(pprint.pformat(
                        self.loaded_obs[name].ls())))
                    #lights only
                    logger.debug('Scenegraph Lights')
                    logger.debug('    {}'.format(
                        pprint.pformat([ name for name in self.loaded_obs[name].ls() if
                        name.lower.find('light')])))
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
                horizon.setScale(5, 5, 5)
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
        self.cvMgr = ConfigVariableManager.getGlobalPtr()
        load_prc_file_data('', 'textures-power-2 none')
        super().__init__()
        blenderpanda.init(self)
        self.accept('escape', sys.exit)
        if logger.isEnabledFor(logging.DEBUG):
            self.accept('d', self.toggle_debug_tools)
        for scene in scenes.available_scenes:
            self.addScene(scene())
# - surfdog -         self.addScene(Scene('surfdog', filename='surfdog',
# - surfdog -             scale=[5.0, 0.1, 5.0],
# - surfdog -             position=[-8, 22, -2]
# - surfdog -         ))
# -cannon-         self.addScene(Scene('cannon', filename='cannon',
# -cannon-             position=[0,22,0],
# -cannon-             hpr=[-45,0,0]
# -cannon-         ))
        self.load_registered_scenes()
        # setup Horizons
        self.horizon = 'skysphere'
        self.addHorizon(Background('skysphere', filename='skysphere_mk2.egg'))
        self.addHorizon(Background('skybox', filename='skybox_1024'))
        self.load_horizon(self.horizon)

        self.console = ConsoleWindow(self)
        # explicit first hide
        self.console.toggleConsole(hide=True)

        self.setControls()
        self.render.set_shader_auto()
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

    def setGlobalControls(self):
        if logger.isEnabledFor(logging.DEBUG):
            logger.debug('Enabling debug controls')
            self.accept("s", self.swap_horizon)
            self.accept("w", self.toggle_sky_wireframe)
        self.accept( self.console.gui_key, self.console.toggleConsole )
        # exit game
        self.accept("escape", sys.exit)
        # load current scene controls


    def setControls(self, console=False):
        """setControls

        :param scene:
        Disable global controls, enable scene controls for given scene
        """
        for winCtrl in self.winControls:
            if winCtrl.win == self.win:
                self.winControls.remove(winCtrl)
        self.setupWindowControls()
        # swap skybox/skysphere
        if console:
            self.ignoreAll()
            self.console.mapControls()
        else:
            self.ignoreAll()
            self.setGlobalControls()
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

    def getNodeTree(self, name=None):
        if not name:
            return [str(child) for child in
                    self.loaded_obs[self.current_scene.name].ls()]
        else:
            if name in self.loaded_obs:
                return self.loaded_obs[name]
        return ['Unknown name "{}"'.format(name)]

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

    def toggle_debug_tools(self):
        if self._dt_enabled:
            loadPrcFileData("", "want-directtools true")
            loadPrcFileData("", "want-tk true")
            self._dt_enabled = False
        else:
            loadPrcFileData("", "want-directtools false")
            loadPrcFileData("", "want-tk false")
            self._dt_enabled = True

def parseArgs(argv=None):
    usage = "%prog [OPTIONS]"
    parser = OptionParser(usage=usage)

    parser.add_option("--threading",
        action="store_true",
        help="Enable threaded and multiprocess code")

    parser.add_option("--debug",
        action="store_true",
        help="Enable debug mode. Implies --verbose.")

    parser.add_option("--verbose",
        action="store_true",
        help="Enable verbose mode.  Redundant if --debug is set.")

    parser.add_option("--log",
        help="Write DEBUG (if set), INFO, WARN and ERR output to file specified", metavar="FILE")

    parser.add_option("--out",
        help="Write ALL output to file specified", metavar="FILE")

    parser.add_option("--config",
        help="Use configuration from FILE", metavar="FILE")

    parser.add_option("--dump-config", action="store_true",
        dest='configdump',
        help="List all configuration options and default values then exit.")

    parser.add_option("--make-config-file", action="store_true",
        dest='saveconfigdump',
        help="Load the game, save the current config, then exit.")

    parser.add_option("--version", action="store_true",
        help="Print version and exit. Note: Version is always printed.")

    parser.add_option('--directtools', action='store_true',
        help="Enable directtools panda3d dev interface.")

    rval = [parser]
    rval.extend(parser.parse_args(argv))
    return rval

if __name__ == '__main__':
    (parser,opts,args) = parseArgs(sys.argv)
    if opts.debug:
        logging.basicConfig(level=logging.DEBUG)
        logger.debug(pprint.pformat(opts))
    elif opts.verbose:
        logging.basicConfig(level=logging.INFO)
    if opts.version:
        if not logger.isEnabledFor(logging.INFO):
            print(VersionInfo.__str__())
        else:
            logger.info(VersionInfo.__str__())
        sys.exit()
    game = SIMGame()
    if opts.configdump:
        logger.debug(
                '**************** Available Config Vars ****************')
        logger.debug(pprint.pformat(game.cvMgr.getVariables()))
        logger.debug(
                '**************** Finito Config ************************')
        sys.exit()
    if opts.saveconfigdump:
        with open('game.cfg', 'w') as cfgfile:
            cfgfile.writelines([str(v) for v in game.cvMgr.getVariables()])
        print(cpMgr)
        sys.exit()
#     loadPrcFileData("", "want-directtools #t")
    if opts.directtools:
        game.toggle_debug_tools()
    game.run()
