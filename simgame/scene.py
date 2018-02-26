"""Collection of classes related to scene heirarchy and placement"""

class SceneInfo(object):
    name            = None
    scale_arr       = None
    pos_arr         = None
    hpr_arr         = None
    filename        = 'assets/'
    lights          = None
    children        = None
    loaded_children = {}

    def __init__(self, name, **kwargs):
        self.name      = name
        self.scale_arr = kwargs.get('scale',
            [1.0, 1.0, 1.0])
        self.pos_arr   = kwargs.get('position',
            [0.0, 0.0, 0.0])
        self.hpr_arr   = kwargs.get('hpr',
            [0.0, 0.0, 0.0])
        self.filename  += kwargs.get('filename', self.name)
        self.lights    = kwargs.get('lights', [])
        self.children  = kwargs.get('children', [])

    def addLight(self, light):
        self.lights.append(light)

    def addChild(self, child):
        self.children.append(child)

    def getMap(self):
        return { 'root' : self.name,
            'children' : list(child.getMap() for child in self.children) }

    def load(self, loader, parent):
        so = loader.load_model(self.filename)
        so.reparent_to(parent)
        so.setScale(*self.scale_arr)
        so.setPos(*self.pos_arr)
        so.setHpr(*self.hpr_arr)
        for child in self.children:
            self.loaded_children[child.name] = child.load(loader, so)
        return so

    def __str__(self):
        return '< SceneInfo for "%s" - "%s" >' % ( self.name, self.filename )

    def __repr__(self):
        return self.__str__()

    def __json__(self):
        # TODO : write json export code
        raise Exception('Not yet implemented')

class ControlMap(object):
    name     = None
    key      = None
    callback = None
    args     = None
    def __init__(self, name, key, callback, args=None):
        super().__init__()
        self.name     = name
        self.key      = key
        self.callback = callback
        self.args     = args

class Scene(SceneInfo):
    controls  = {}
    adj_angle = 0.0
    adj_pitch = 0.0

    _camera = None
    @property
    def camera(self): return self._camera
    @camera.setter
    def camera(self, camera): self._camera = camera

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for cm in kwargs.get('controls', []):
            self.controls[cm.name] = cm

    def cmIter(self):
        for cm in self.controls:
            yield cm

    def register_camera(self, camera):
        self.camera = camera

    def controlmapIter(self):
        for itm in self.controls.items():
            yield itm

    def registerTasks(self, taskMgr):
        raise Exception("Abstract parent method called.")

class SceneObject(SceneInfo):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

class Background(SceneInfo):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

class SceneError(Exception):
    def __init__(self):
        super().__init__()
