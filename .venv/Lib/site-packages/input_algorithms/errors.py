from delfick_error import DelfickError, ProgrammerError

# Explicitly say I want ProgrammerError in this context
ProgrammerError = ProgrammerError

class BadSpec(DelfickError):
    desc = "Something wrong with this specification"

class BadSpecValue(BadSpec):
    desc = "Bad value"

class BadDirectory(BadSpecValue):
    desc = "Expected a path to a directory"

class BadFilename(BadSpecValue):
    desc = "Expected a path to a filename"

class DeprecatedKey(BadSpecValue):
    desc = "Key is deprecated"

class BadSpecDefinition(BadSpecValue):
    desc = "Spec isn't defined so well"

