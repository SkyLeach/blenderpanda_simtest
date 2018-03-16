# global env imp
from math import pi, sin, cos
import logging
logger = logging.getLogger(__name__)
import pprint
# venv lib imports
from direct.task import Task
from direct.actor.Actor import Actor
from direct.interval.IntervalGlobal import Sequence
#from pandac.PandaModules import Quat
from panda3d.core import *

# local imp
from .scene import ControlMap, Scene

class Corvette(Scene):
    default_controls = None
    angle        = 0.0
    pitch        = 0.0
    adjust_angle = 0.0
    adjust_pitch = 0.0
    last_time    = 0.0
    cam_speed = 0.5

    ship_anchor_node = None

    major_section_names = [
        'EmptyTransformSphere',
        'EmptyHabringClusterSphere',
        'CenterSpine', # start here for now
        'Engineering',
        'Lamp',
        'Leaf Panel',
        'Tank',
        'Shieldcap',
        ]
    obj_clusters = [[
        'EmptyHabringClusterSphere',
        'Habgear Ring Segments',
        'HabringPointlight',
        'HR Segment',
        'HR Strut',
    ]]
    @property
    def camera(self): return self._camera
    @camera.setter
    def camera(self, camera):
        self._camera = camera
        # setup Camera for this scene
        self.camera.set_pos(sin(self.angle)*20,-cos(self.angle)*20,0)
        self.camera.look_at(0,0,0)

    def __init__(self):
        self.default_controls = {
            'l.turn' : ControlMap('l.turn', 'arrow_left', self.adjust_turning,
                args=[-1.0, 0.0]),
            'lu.turn' : ControlMap('lu.turn', "arrow_left-up",
                self.adjust_turning, args=[1.0, 0.0]),
            'r.turn' : ControlMap('r.turn', "arrow_right", self.adjust_turning,
                args=[1.0, 0.0]),
            'ru.turn' : ControlMap('ru.turn', "arrow_right-up",
                self.adjust_turning, args=[-1.0, 0.0]),
            'u.turn' : ControlMap('u.turn', "arrow_up", self.adjust_turning,
                args=[0.0, 1.0]),
            'uu.turn' : ControlMap('uu.turn', "arrow_up-up",
                self.adjust_turning, args=[0.0, -1.0]),
            'd.turn' : ControlMap('d.turn', "arrow_down", self.adjust_turning,
                args=[0.0, -1.0]),
            'du.turn' : ControlMap('du.turn', "arrow_down-up",
                self.adjust_turning, args=[0.0, 1.0]),
        }
        super().__init__('corvette', filename='corvette.bam',
            controls=list(self.default_controls.values()))

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
            self.camera.look_at(0,0,0)
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
        angleRadians = angleDegrees * (pi / 180.0)
        self.cannon.setH(angleDegrees)
        return Task.cont

#     def spinHabringTask(self, task):
#         angleDegrees = 
#         angleRadians = 
#         self.cannon.setH(angleDegrees)
#         return Task.cont

    def register_tasks(self, taskMgr):
        # setup global Tasks
        # Add the spinCameraTask procedure to the task manager
        # taskMgr.add(self.spinCameraTask, "SpinCameraTask")
        # taskMgr.add(self.spinCannonTask, "SpinCannonTask")
        # Key events and camera movement task
        taskMgr.add(self.update_camera, 'adjust camera', sort = 10)
        pass

    def habring_rotate(self, habringnode, g=0.7):
        gone_ang_velocity=1.576088025433646
        gpoint7_ang_velcoity=1.318649849179353
        #1g in deg/s
        gone_degpersec = 9.456528152601875
        rotseconds = 360 / gone_degpersec
        #q = Quat()
        #q.reparentTo(habringnode)
        #q.setHpr(Vec3(360,0,0))
        #rseq = Sequence(habringnode.quatInterval(rotseconds,q),name='Hab Ring Rotate')
        rseq = Sequence(habringnode.hprInterval(rotseconds,Vec3(360,0,0)),name='Hab Ring Rotate')
        rseq.loop()

    def setup(self, rootnode):
        habring = None
        for ndex,name in enumerate(self.major_section_names):
            if not ndex:
                self.ship_anchor_node = rootnode.find(name)
                logger.debug('parent is {}:{}'.format(name,self.ship_anchor_node))
                continue
            if not self.ship_anchor_node:
                raise Exception('This shouldn\'t happen.')
            child = rootnode.find(name)
            child.wrtReparentTo(self.ship_anchor_node)
        for cluster in self.obj_clusters:
            cluster_parent = None
            for ndex,name in enumerate(cluster):
                if not ndex:
                    cluster_parent = self.ship_anchor_node.find(name)
                    logger.debug(
                        'cluster parent is {}:{}'.format(name,cluster_parent))
                    continue
                child = rootnode.find(name)
                child.wrtReparentTo(cluster_parent)
            self.habring_rotate(cluster_parent)

        #now set the parent to scene center
        self.ship_anchor_node.setPos(Vec3(0,0,0))
