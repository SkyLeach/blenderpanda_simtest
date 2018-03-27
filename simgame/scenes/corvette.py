# global env imp
from math import pi, sin, cos
import logging
import pprint
import traceback
# venv lib imports
from direct.task import Task
from direct.actor.Actor import Actor
from direct.interval.IntervalGlobal import Sequence, Parallel, Func
# from pandac.PandaModules import Quat
from panda3d.core import Vec3, PointLight, VBase4, AntialiasAttrib
# it's generally a good idea to use explicit imports
# from panda3d.core import *

# local imp
from .scene import ControlMap, Scene

logger = logging.getLogger(__name__)


class Corvette(Scene):
    default_controls  = None
    angle             = 0.0
    pitch             = 0.0
    adjust_angle      = 0.0
    adjust_pitch      = 0.0
    last_time         = 0.0
    cam_speed         = 0.5
    # multiplier to scale up mesh for mass calculations.
    ship_anchor_node  = None
    translights = []  # lights subject to transformation events using delta-v

    # seconds and mass in metric tonnes
    sceneobj_lights = [{
        'name'       : 'HRSegLight',
        'color'      : VBase4(0.6, 0.7, 1, 1),
        'parent'     : 'Leaf Panel',
        # 'translate' : (Vec3(87.8968,-7.49207,23.467),Vec3(0,0,0)),
        'translate'  : (Vec3(0, 0, -330), Vec3(0, 0, 0)),
        'type'       : PointLight
    }, ]
    major_section_names = [
        ('EmptyTransformSphere'       , 0)        ,
        ('EmptyHabringClusterSphere'  , 0)        ,
        ('CenterSpine'                , 30345)    ,  # start here for now
        ('Engineering'                , 0)        ,
        ('Leaf Panel'                 , 0)        ,
        ('Tank'                       , 0)        ,
        ('Shieldcap'                  , 1121.2*4) ,
        ('Empty Engine Anchor Sphere' , 0)        ,
        ('Empty Tank Anchor Sphere'   , 0)        ,
        # ('Shieldcap Lamp'           , 0)        ,
        # ('Engine Area Light'        , 0)        ,
        ('Cube Engine'                , 0)        ,
        ('Trap-Engine'                , 0)        ,
    ]
    obj_clusters = [[
        ('EmptyHabringClusterSphere' , 0) ,
        ('Habgear Ring Segments'     , 0) ,
        ('HabringPointlight'         , 0) ,
        # ('PointLight Point'        , 0) ,
        ('HR Segment'                , 0) ,
        ('HR Strut'                  , 0) ,
    ]]
    obj_spacesuit = [
        ('SpaceSuitLight.L'               , 0) ,
        ('Spacesuit.Helmet.Light.R'       , 0) ,
        ('Cadera'                         , 0) ,
        ('Cadera.001'                     , 0) ,
        ('SpacesuitPoseBase'              , 0) ,
        ('SpacesuitPosebase2'             , 0) ,
        ('Spacesuit.Armature.Femur.L'     , 0) ,
        ('Spacesuit.Armature.Femur.R'     , 0) ,
        ('Spacesuit.Mano'                 , 0) ,
        ('Spacesuitmetarig'               , 0) ,
        ('Casco'                          , 0) ,
        ('Cubre todo.001'                 , 0) ,
        ('Cubre todo.002'                 , 0) ,
        ('Parasol costado.001'            , 0) ,
        ('Lamparas'                       , 0) ,
        ('Parasol'                        , 0) ,
        ('Traje (Suit)'                   , 0) ,
        ('Vidrio (Glass)'                 , 0) ,
        ('SpacesuitRightfootPlaneHook.01' , 0) ,
        ('SpacesuitLeftfootPlaneHook.02'  , 0) ,
        ('Spacesuit.Pierna.L'             , 0) ,
        ('Spacesuit.Pierna.R'             , 0) ,
        ('Spacesuit.Plane.001'            , 0) ,
        ('SpacesuitPolo.L'                , 0) ,
        ('SpacesuitPolo.R'                , 0) ,
    ]
    cluster_specials = None

    @property
    def camera(self):
        return self._camera

    @camera.setter
    def camera(self, camera):
        self._camera = camera
        # setup Camera for this scene
        self.camera.set_pos(sin(self.angle)*20, -cos(self.angle)*20, 0)
        self.camera.look_at(0, 0, 0)

    def __init__(self):
        self.actor_scene = True
        self.default_controls = {
            'l.turn' : ControlMap(
                'l.turn', 'arrow_left', self.adjust_turning,
                args=[-1.0, 0.0]),
            'lu.turn' : ControlMap(
                'lu.turn', "arrow_left-up",
                self.adjust_turning, args=[1.0, 0.0]),
            'r.turn' : ControlMap(
                'r.turn', "arrow_right", self.adjust_turning,
                args=[1.0, 0.0]),
            'ru.turn' : ControlMap(
                'ru.turn', "arrow_right-up",
                self.adjust_turning, args=[-1.0, 0.0]),
            'u.turn' : ControlMap(
                'u.turn', "arrow_up", self.adjust_turning,
                args=[0.0, 1.0]),
            'uu.turn' : ControlMap(
                'uu.turn', "arrow_up-up",
                self.adjust_turning, args=[0.0, -1.0]),
            'd.turn' : ControlMap(
                'd.turn', "arrow_down", self.adjust_turning,
                args=[0.0, -1.0]),
            'du.turn' : ControlMap(
                'du.turn', "arrow_down-up",
                self.adjust_turning, args=[0.0, 1.0]),
        }
        super().__init__(
            'corvette', filename='corvette.bam',
            controls=list(self.default_controls.values()))

        self.cluster_specials = {
            'EmptyHabringClusterSphere' : self.habring_rotate,
        }

    def adjust_turning(self, heading, pitch):
        self.adjust_angle += heading
        self.adjust_pitch += pitch

    def update_camera(self, task):
        if task.time != 0.0:
            dt = task.time - self.last_time
            self.last_time = task.time
            self.angle += pi * dt * self.adjust_angle * self.cam_speed
            self.pitch += pi * dt * self.adjust_pitch * self.cam_speed
            # Why /2.001 and not an even 2.0? Because then we'd have to set_Hpr
            # explicitly, as look_at can't deduce the heading when the camera is
            # exactly above/below the spheres center.
            if self.pitch > pi/2.001:
                self.pitch = pi/2.001
            if self.pitch < -pi/2.001:
                self.pitch = -pi/2.001
            self.camera.set_pos(sin(self.angle)*cos(abs(self.pitch))*20,
                                -cos(self.angle)*cos(abs(self.pitch))*20,
                                sin(self.pitch)*20)
            self.camera.look_at(0, 0, 0)
        return Task.cont

    # Define a procedure to move the camera.
    def spinCameraTask(self, task):
        angleDegrees = task.time * 6.0
        angleRadians = angleDegrees * (pi / 180.0)
        self.camera.setPos(20 * sin(angleRadians), -20.0 * cos(angleRadians), 3)
        self.camera.setHpr(angleDegrees, 0, 0)
        return Task.cont

    def spinCannonTask(self, task):
        angleDegrees = task.time * 6.0
        # angleRadians = angleDegrees * (pi / 180.0)
        self.cannon.setH(angleDegrees)
        return Task.cont

    def register_tasks(self, taskMgr):
        # setup global Tasks
        # Add the spinCameraTask procedure to the task manager
        # taskMgr.add(self.spinCameraTask, "SpinCameraTask")
        # taskMgr.add(self.spinCannonTask, "SpinCannonTask")
        # Key events and camera movement task
        taskMgr.add(self.update_camera, 'adjust camera', sort=10)
        pass

    def habring_rotate(self, habringnode, g=0.7):
        # old quaternion variables, not used because of offset
        # gone_ang_velocity=1.576088025433646
        # gpoint7_ang_velcoity=1.318649849179353
        # 1g in deg/s
        gone_degpersec = 9.456528152601875
        rotseconds = 360 / gone_degpersec
        # q = Quat()
        # q.reparentTo(habringnode)
        # q.setHpr(Vec3(360,0,0))
        # rseq = Sequence(habringnode.quatInterval(rotseconds,q),name='Hab Ring Rotate')
        rseq = Sequence(habringnode.hprInterval(
            rotseconds, Vec3(360, 0, 0)),
            name='Hab Ring Rotate')
        rseq.loop()

    def moveLights(self):
        return
        deltav = self.ship_anchor_node.getPosDelta()
        deltaq = self.ship_anchor_node.getQuat()
        # self.ship_anchor_node.find('HR Segment'))
        for light in self.translights:
            light.setPos(deltav)
            light.setQuat(deltaq)

    def setup(self, rootnode):
        # TODO: move this to parent
        rootnode.setAntialias(AntialiasAttrib.MAuto)
        for ndex, (name, mass) in enumerate(self.major_section_names):
            if not ndex:
                self.ship_anchor_node = rootnode.find(name)
                logger.debug('parent is {}:{}'.format(
                    name, self.ship_anchor_node))
                for linfo in self.sceneobj_lights:
                    light = linfo['type'](linfo['name'])
                    light.setColor(linfo['color'])
                    # christ that's awful
                    # light.setShadowCaster(True)
                    # light.setAttenuation((1, 0, 1))
                    # parent = rootnode.find(linfo['parent'])
                    lnode = rootnode.attachNewNode(light)
                    lnode.setPosHpr(*linfo['translate'])
                    # parent.setLight(lnode)
                    rootnode.setLight(lnode)
                    self.translights.append(lnode)
                    # lnode path will have changed.  Re-find it.
                    logger.debug('prevpath: {}'.format(lnode))
                    logger.debug('prevpath: {}'.format(
                        rootnode.find(linfo['name'])))
                    # rootnode.find(linfo['name'])
                continue
            if not self.ship_anchor_node:
                raise Exception('This shouldn\'t happen.')
            child = rootnode.find(name)
            if str(child) == '**not found**':
                logger.warn('****** "{}" NOT FOUND! ******'.format(name))
                continue
            logger.debug('Reparenting {} ({}) to {}'.format(name, child,
                self.ship_anchor_node))
            child.wrtReparentTo(self.ship_anchor_node)
        for cluster in self.obj_clusters:
            cluster_parent = None
            cluster_parent_name = None
            for ndex,(name, mass) in enumerate(cluster):
                if not ndex:
                    cluster_parent = self.ship_anchor_node.find(name)
                    cluster_parent_name = name

                    logger.debug(
                        'cluster parent is {}:{}'.format(name,cluster_parent))
                    continue
                child = rootnode.findAllMatches(name)
                if str(child) == '**not found**':
                    logger.warn('****** "{}" NOT FOUND! ******'.format(name))
                    continue
                logger.debug('Reparenting {} ({}) to {}'.format(name, child,
                    self.ship_anchor_node))
                child.wrtReparentTo(cluster_parent)
# -weirdlight-                 if name.lower().find('light')>=0:
# -weirdlight-                     clight = cluster_parent.find(name)
# -weirdlight-                     logger.debug('Setting light {}=({})'.format(name,clight))
# -weirdlight-                     try:
# -weirdlight-                         cluster_parent.setLight(clight)
# -weirdlight-                     except:
# -weirdlight-                         traceback.print_exc()
# -weirdlight-                         pass
            if cluster_parent_name in self.cluster_specials:
                self.cluster_specials[cluster_parent_name](cluster_parent)
            else:
                logger.warn(
                    'Cluster handle {}:({}) has no special func.'.format(
                        cluster_parent_name,
                        cluster_parent))

        # now set the parent to scene center
        # self.ship_anchor_node.setPosHpr(Vec3(0,100,0),Vec3(0,0,90))
#         shipactor = Actor()
#         rootnode.attachNode(shipactor)
#         self.ship_anchor_node.wrtReparentTo(shipactor)
        time=15
        pos = Vec3(0,100,0)
        hpr = Vec3(0,0,90)
        Parallel(
                self.ship_anchor_node.posInterval(time, pos),
                self.ship_anchor_node.hprInterval(time, hpr),
                Func(self.moveLights)
            ).loop()
#         for lnode in self.translights:
#             Parallel(lnode.posInterval(time, pos),
#             lnode.hprInterval(time, hpr)).loop()