from timepiece.sections.base import default_available_sections
from timepiece.helpers import memoized_property

from input_algorithms.errors import BadSpecValue
from input_algorithms.meta import Meta
from delfick_error import DelfickError

from parsimonious.nodes import Node, NodeVisitor
from parsimonious.grammar import Grammar
import parsimonious

EmptyMeta = Meta({}, [])

class TimeSpecGrammar(object):
    Visitor = NotImplemented

    def __init__(self, available_sections=None):
        self.available_sections = available_sections

    @memoized_property
    def visitor(self):
        return self.Visitor(self.available_sections)

    def time_spec_to_object(self, time_spec, validate=True):
        return self.visitor.parse(time_spec.replace(" ", "").replace("\t", ""), validate=validate)

    def clone(self, more_sections):
        instance = self.__class__(self.available_sections)
        instance._visitor = self.visitor.clone(more_sections)
        return instance

class TimeSpecVisitor(NodeVisitor):
    ErrorKls = DelfickError
    Joiner = NotImplemented
    Section = NotImplemented

    @memoized_property
    def grammar(self):
        return Grammar(self.grammar_string)

    grammar_string = """
        time_spec = grouped_funcs?

        grouped_funcs = grouped_funcs_first grouped_with_joiner*
        grouped_with_joiner = joiner grouped_funcs
        grouped_funcs_first = wrapped_grouped_funcs / func
        wrapped_grouped_funcs = start_bracket grouped_funcs end_bracket

        func = func_name "(" func_sig ")"
        func_sig = key_pairs?

        key_pairs = key_pair commad_key_pair*
        commad_key_pair = "," key_pair
        key_pair = key_name ":" func_or_value

        func_or_value = arbitrary_string / number / func

        start_bracket = "("
        end_bracket = ")"
        joiner = "&" / "|"
        key_name = ~r"[a-zA-Z][a-zA-Z0-9]+"
        func_name = ~r"[a-zA-Z][a-zA-Z0-9_]+"
        number = ~r"[0-9]+" &~r"[\),]"
        arbitrary_string = ~r"[\s\.a-zA-Z0-9;_-]+" !"("
    """

    def __init__(self, available_sections=None):
        self.count = -1
        self.joiner_count = -1
        self.meta = EmptyMeta
        self.time_spec = None

        self.available_sections = available_sections
        if self.available_sections is None:
            self.available_sections = default_available_sections

        self.visiting_methods = {}
        for attr in dir(self):
            if attr.startswith("visit_"):
                self.visiting_methods[attr[6:]] = getattr(self, attr)

    def clone(self, more_sections=None):
        sections = {}
        sections.update(dict(self.available_sections or {}))
        sections.update(dict(more_sections or {}))
        instance = self.__class__(sections)
        instance._grammar = getattr(self, "_grammar", None)
        return instance

    def parse(self, text, validate=True):
        try:
            res = super(TimeSpecVisitor, self).parse(text)
        except (parsimonious.exceptions.VisitationError, parsimonious.exceptions.IncompleteParseError) as error:
            raise BadSpecValue(error=error)
        else:
            if validate:
                if not hasattr(res, "specifies"):
                    raise self.ErrorKls("Sorry, object can only be used as a parameter", got=res)
                if "repeat" not in res.specifies and "once" not in res.specifies:
                    raise self.ErrorKls("Time spec is invalid, it must be able to specify a start with an optional interval", got=res.specifies)
            return res

    def visit(self, node):
        if not isinstance(node, Node):
            return node

        method = self.visiting_methods.get(node.expr_name)
        if method is None:
            while node.expr_name == "" and node.children and len(node.children) == 1:
                node = node.children.pop(0)
            return [self.visit(n) for n in node.children if n.text != ""]
        if method == "first_child":
            return self.visit(node.children[0])
        elif method == "second_child":
            return self.visit(node.children[1])
        elif method == "just_text":
            return node.text.strip()
        elif method == "children":
            return [self.visit(n) for n in node]
        elif method == "integer":
            return int(node.text.strip())
        else:
            return method(node, node.children)

    visit_integer = "integer"
    visit_grouped_with_joiner = "children"
    visit_grouped_funcs_first = "first_child"
    visit_commad_key_pair = visit_wrapped_grouped_funcs = "second_child"
    visit_arbitrary_string = visit_func_name = visit_key_name = visit_key_value = visit_whitespace = "just_text"

    def visit_time_spec(self, node, children):
        if node.text == "":
            raise self.ErrorKls("No specification was given")
        return self.visit(children[0]).simplify()

    def visit_func_sig(self, node, children):
        if not children or children[0].text.strip() is "":
            return {}
        else:
            return self.visit(children[0])

    def visit_key_pairs(self, node, children):
        first = self.visit(children[0])
        if children[1].text == "":
            return dict([first])
        else:
            visited = self.visit(children[1])
            if visited and visited[0] == []:
                return dict([first, visited[1]])
            return dict([first] + self.visit(children[1]))

    def visit_key_pair(self, node, children):
        return (self.visit(children[0]), self.visit(children[2])[0])

    def visit_grouped_funcs(self, node, children):
        first = self.visit(children[0])
        second = self.visit(children[1])

        if second:
            joiner, second = second
            return self.Joiner().normalise(self.meta.indexed_at("{0}({1})".format(self.joiner_count, joiner)), (joiner, first, second))
        else:
            return first

    def visit_func(self, node, children):
        self.count += 1
        nxt = (self.visit(children[0]), self.visit(children[2]))
        return self.Section(self.available_sections).normalise(self.meta.indexed_at("{0}({1})".format(self.count, nxt[0])), nxt)

    def visit_joiner(self, node, children):
        self.joiner_count += 1
        return {"|": "OR", "&": "AND", "+": "PLUS", "-": "MINUS"}[node.text.strip()]

