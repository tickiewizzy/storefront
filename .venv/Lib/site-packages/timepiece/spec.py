from timepiece.grammar import TimeSpecGrammar, TimeSpecVisitor
from timepiece.sections.base import JoinerSpec, SectionSpec
from timepiece.sections import sections as sections_module

from delfick_error import DelfickError

# Make vim quiet
# only imported so sections are registered
sections_module = sections_module

def make_timepiece(ErrorKls=DelfickError, JoinerSpec=JoinerSpec, SectionSpec=SectionSpec, sections=None):
	Joiner = type("Joiner", (JoinerSpec, ), {"ErrorKls": ErrorKls})
	Section = type("Section", (SectionSpec, ), {"ErrorKlss": ErrorKls})
	Visitor = type("Visitor", (TimeSpecVisitor, ), {"ErrorKls": ErrorKls, "Joiner": Joiner, "Section": Section})
	return type("Grammar", (TimeSpecGrammar, ), {"Visitor": Visitor})(sections)

