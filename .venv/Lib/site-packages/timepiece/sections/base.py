from input_algorithms.errors import BadSpecValue
from input_algorithms import spec_base as sb
from input_algorithms.dictobj import dictobj
from input_algorithms.meta import Meta

from delfick_error import DelfickError

EmptyMeta = Meta.empty()

default_available_sections = {}
class a_section(object):
    def __init__(self, name):
        self.name = name

    def __call__(self, kls):
        default_available_sections[self.name] = kls.FieldSpec()
        kls._section_name = self.name.replace("Spec", "")
        return kls

class BaseSpec(dictobj.Spec):

    def simplify(self):
        return self

    def or_with(self, other):
        raise BadSpecValue("Sorry, can't do {0} | {1}".format(self.__class__.__name__, other.__class__.__name__))

    def combine_with(self, other):
        raise BadSpecValue("Sorry, can't do {0} & {1}".format(self.__class__.__name__, other.__class__.__name__))

    @classmethod
    def using(kls, **kwargs):
        return kls.FieldSpec().normalise(EmptyMeta, kwargs)

class ssv_spec(sb.Spec):
    """Semicolon separated values"""
    def setup(self, choices=None, spec=None):
        self.spec = spec
        self.choices = choices

    def normalise_filled(self, meta, val):
        if self.choices is None:
            if type(val) is list:
                res = [v.strip() for v in val]
            else:
                res = [v.strip() for v in val.split(";")]
        else:
            if type(val) is not list:
                val = [v.strip() for v in val.split(";")]
            else:
                val = [v.strip() for v in val]
            res = sb.listof(sb.string_choice_spec(self.choices)).normalise(meta, val)

        if self.spec is None:
            return res

        return sb.listof(self.spec).normalise(meta, res)

class none_spec(sb.Spec):
    def normalise(self, meta, val):
        if val is None:
            return None
        else:
            raise BadSpecValue("Expected None", got=val, meta=meta)

class JoinerSpec(sb.Spec):
    ErrorKls = DelfickError

    def normalise_filled(self, meta, val):
        section_spec = SectionSpec()
        val = sb.tuple_spec(sb.string_choice_spec(["OR", "AND"]), section_spec, section_spec).normalise(meta, val)
        typ, first, second = val
        try:
            if typ == "OR":
                return first.or_with(second)
            else:
                return first.combine_with(second)
        except self.ErrorKls as error:
            raise BadSpecValue("Failed to join", error=error)

class SectionSpec(sb.Spec):
    ErrorKls = DelfickError

    def setup(self, available_sections=None):
        if available_sections is None:
            self.available_sections = default_available_sections
        else:
            self.available_sections = available_sections

    def normalise_filled(self, meta, val):
        if isinstance(val, dictobj):
            return val

        if isinstance(val, tuple) and len(val) is 1:
            val = (val[0], {})

        val = sb.tuple_spec(
              sb.string_spec()
            , sb.dictof(
                  sb.string_spec()
                , sb.match_spec(
                      (bool, sb.boolean())
                    , (int, sb.integer_spec())
                    , (str, sb.string_spec())
                    , (tuple, self)
                    , (dictobj, sb.any_spec())
                    )
                )
            ).normalise(meta, val)

        if val[0] not in self.available_sections:
            raise BadSpecValue("Unknown section type", meta=meta, wanted=val[0], available=list(self.available_sections.keys()))

        made = self.available_sections[val[0]].normalise(meta, val[1])
        simplified = None
        while made is not simplified:
            if simplified is not None:
                made = simplified
            if hasattr(made, "simplify"):
                simplified = made.simplify()
            else:
                break
        return simplified

def section_repr(self):
    def convert(o):
        if o.__class__.__repr__ is section_repr:
            return repr(o)
        else:
            return o

    kwargs = sorted((k, convert(v)) for k, v in self.items() if not k.startswith("_") and v is not sb.NotSpecified)
    formatted = ['"{0}": {1}'.format(k, v) for k, v in kwargs]
    return "{0}({1})".format(self.__class__._section_name, "{{{0}}}".format(', '.join(formatted)))

class fieldSpecs_from(sb.Spec):
    def setup(self, *specs):
        self.specs = specs

    @property
    def spec(self):
        if len(self.specs) is 1:
            return self.specs[0].FieldSpec()
        else:
            return sb.or_spec(*[fieldSpecs_from(spec) for spec in self.specs])

    def normalise_filled(self, meta, val):
        if isinstance(val, BaseSpec):
            if any(isinstance(val, k) for k in self.specs):
                return val
            else:
                raise BadSpecValue("Expected a particular kind of object, got something different", available=[k.__name__ for k in self.specs], got=type(val), meta=meta)
        return self.spec.normalise(meta, val)

