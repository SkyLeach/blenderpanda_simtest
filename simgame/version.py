# Module Version Information
class VersionInfo:
    _major = 0
    _minor = 0
    _iter  = 1
    _name  = 'S.I.M.'
    def version(self=None):
        return [VersionInfo._major,VersionInfo._minor,VersionInfo._iter]

        return

    def __str__(self=None):
        vinf = []
        if(self):
            vinf.append(self.name())
            vinf.extend(self.version())
        else:
            vinf.append(VersionInfo.name())
            vinf.extend(VersionInfo.version())
        return '{} - {}.{}.{}'.format(*vinf)

    def __repr__(self=None):
        if self:
            return str(self.version)
        else:
            return str(VersionInfo.version)

    def name(self=None):
        if self:
            return self._name
        else:
            return VersionInfo._name
