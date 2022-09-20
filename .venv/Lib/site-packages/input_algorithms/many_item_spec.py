"""
We define here a custom spec type here for interpreting list specifications.
"""

from input_algorithms.spec_base import NotSpecified, Spec, formatted
from input_algorithms.errors import BadSpecValue
import six

class many_item_formatted_spec(Spec):
    """
    Usage
        .. code-block:: python

            class FinalKls(dictobj):
                fields = ["one", "two", ("three", None)]

            class my_special_spec(many_item_formatted_spec):
                specs = [integer_spec(), string_spec()]

                def create_result(self, one, two, three, meta, val, dividers):
                    if three is NotSpecified:
                        return FinalKls(one, two)
                    else:
                        return FinalKls(one, two, three)

                # The rest of the options are optional
                creates = FinalKls
                value_name = "special"
                seperators = "^"
                optional_specs = [boolean()]

            spec = my_special_spec()
            spec.normalise(meta, "1^tree") == FinalKls(1, "tree")
            spec.normalise(meta, [1, "tree"]) == FinalKls(1, "tree")
            spec.normalise(meta, [1, tree, False]) == FinalKls(1, "tree", False)

        We can also define modification hooks for each part of the spec:

        .. code-block:: python

            class my_special_spec(many_item_formatted_spec):
                specs = [integer_spec(), integer_spec(), integer_spec()]

                def spec_wrapper_2(self, spec, one, two, meta, val, dividers):
                    return defaulted(spec, one + two)

                def determine_2(self, meta, val):
                    return 42

                def alter_2(self, one, meta, original_two, val):
                    if one < 10:
                        return original_two
                    else:
                        return original_two * 10

                def alter_3(self, one, two, meta, original_three, val):
                    if two < 100:
                        return original_three
                    else:
                        return original_three * 100

                def create_result(self, one, two, three, meta, val, dividers):
                    return FinalKls(one, two, three)

    A spec for something that is many items
    Either a list or a string split by ":"

    If it's a string it will split by ':'
    Otherwise if it's a list, then it will use as is
    and will complain if it has two many values

    It will use determine_<num> on any value that is still NotSpecified after
    splitting the val.

    And will use alter_<num> on all values after they have been formatted.

    Where <num> is 1 indexed index of the value in the spec specifications.

    Finally, create_result is called at the end to create the final result from
    the determined/formatted/altered values.
    """
    specs = []
    creates = None
    value_name = None
    seperators = ":"
    optional_specs = []

    def setup(self, *args, **kwargs):
        """Setup our value_name if not already specified on the class"""
        if not self.value_name:
            self.value_name = self.__class__.__name__

    def create_result(*args):
        """Called by normalise with (*vals, meta, original_val, dividers)"""
        raise NotImplementedError()

    def normalise(self, meta, val):
        """Do the actual normalisation from a list to some result"""
        if self.creates is not None:
            if isinstance(val, self.creates):
                return val

        vals, dividers = self.split(meta, val)
        self.validate_split(vals, dividers, meta, val)

        for index, spec in enumerate(self.specs + self.optional_specs):
            expected_type = NotSpecified
            if isinstance(spec, (list, tuple)):
                spec, expected_type = spec

            args = [vals, dividers, expected_type, index+1, meta, val]

            self.determine_val(spec, *args)
            spec = self.determine_spec(spec, *args)
            self.alter(spec, *args)

        return self.create_result(*list(vals) + [meta, val, dividers])

    def determine_spec(self, spec, vals, dividers, expected_type, index, meta, original_val):
        return getattr(self, "spec_wrapper_{0}".format(index), lambda spec, *args: spec)(spec, *list(vals)[:index] + [meta, original_val, dividers])

    def determine_val(self, spec, vals, dividers, expected_type, index, meta, original_val):
        """
        Find a val and spec for this index in vals.

        Use self.determine_<index> to get a val

        Use self.spec_wrapper_<index> to get a spec

        Or just use the spec passed in and the value at the particular index in vals
        """
        val = NotSpecified
        if index <= len(vals):
            val = vals[index-1]
        if len(vals) < index:
            vals.append(val)

        val = getattr(self, "determine_{0}".format(index), lambda *args: val)(*list(vals)[:index] + [meta, original_val])
        vals[index-1] = val

    def alter(self, spec, vals, dividers, expected_type, index, meta, original_val):
        """
        Alter the val we found in self.determine_val

        If we have a formatter on the class, use that, otherwise just use the spec.

        After this, use self.alter_<index> if it exists
        """
        val = vals[index-1]
        specified = val is not NotSpecified
        not_optional = index - 1 < len(self.specs)
        no_expected_type = expected_type is NotSpecified
        not_expected_type = not isinstance(val, expected_type)

        if (not_optional or specified) and (no_expected_type or not_expected_type):
            val = self.normalise_val(spec, meta, val)

        altered = getattr(self, "alter_{0}".format(index), lambda *args: val)(*(vals[:index] + [val, meta, original_val]))
        vals[index-1] = altered

    def normalise_val(self, spec, meta, val):
        """
        Normalise with a spec

        If we have a formatter, use that as well
        """
        if getattr(self, "formatter", None):
            return formatted(spec, formatter=self.formatter).normalise(meta, val)
        else:
            return spec.normalise(meta, val)

    def validate_split(self, vals, dividers, meta, val):
        """Validate the vals against our list of specs"""
        if len(vals) < len(self.specs) or len(vals) > len(self.specs) + len(self.optional_specs):
            raise BadSpecValue("The value is a list with the wrong number of items"
                , got=val
                , meta=meta
                , got_length=len(vals)
                , min_length=len(self.specs)
                , max_length=len(self.specs) + len(self.optional_specs)
                , looking_at = self.value_name
                )

    def split(self, meta, val):
        """Split our original value based on our seperators"""
        if isinstance(val, (list, tuple)):
            vals = val
            dividers = [':'] * (len(val) - 1)

        elif isinstance(val, six.string_types):
            vals = []
            dividers = []
            if self.seperators:
                while val and any(seperator in val for seperator in self.seperators):
                    for seperator in self.seperators:
                        if seperator in val:
                            nxt, val = val.split(seperator, 1)
                            vals.append(nxt)
                            dividers.append(seperator)
                            break
                vals.append(val)

            if not vals:
                vals = [val]
                dividers=[None]

        elif isinstance(val, dict):
            if len(val) != 1:
                raise BadSpecValue("Value as a dict must only be one item", got=val, meta=meta)
            vals = list(val.items())[0]
            dividers = [':']

        else:
            vals = [val]
            dividers = []

        return vals, dividers

