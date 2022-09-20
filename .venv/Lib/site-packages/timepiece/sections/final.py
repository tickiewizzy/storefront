from timepiece.sections.base import BaseSpec, ssv_spec, none_spec, section_repr, fieldSpecs_from
from timepiece.helpers import memoized_property

from input_algorithms import spec_base as sb
from input_algorithms.dictobj import dictobj
from input_algorithms.meta import Meta

from datetime import datetime, timedelta

EmptyMeta = Meta.empty()

weekday_names = ["mon", "tues", "wed", "thur", "fri", "sat", "sun"]

def repeat_every_spec():
    return fieldSpecs_from(IntervalsSpec)

def repeat_start_spec():
    from timepiece.sections import sections
    return fieldSpecs_from(sections.EpochSpec, DateTimeSpec, sections.SunRiseSpec, sections.SunSetSpec)

def repeat_end_spec():
    from timepiece.sections import sections
    return sb.or_spec(none_spec(), fieldSpecs_from(sections.Forever, sections.EpochSpec, DateTimeSpec, sections.SunRiseSpec, sections.SunSetSpec))

class RepeatSpec(BaseSpec):
    __repr__ = section_repr
    @memoized_property
    def specifies(self):
        spec = ()
        if self.every is not None:
            spec += ("repeat", )
        if self.end is not None:
            spec += ("duration", )
        if not spec:
            spec = ("once", )
        return spec
    every = dictobj.Field(repeat_every_spec, default=None)
    start = dictobj.Field(repeat_start_spec, wrapper=sb.required)
    end = dictobj.Field(repeat_end_spec, default=None)

    def is_filtered(self, at):
        if self.end and at > self.end.datetime:
            return False

        if at < self.start.datetime:
            return False

        return self.every.is_filtered(at)

    def following(self, at=None):
        if at is None:
            at = datetime.utcnow()

        if self.end and at > self.end.datetime:
            return

        if at < self.start.datetime:
            return self.start.following(at)

        if self.every:
            return self.every.following(at, self.start.datetime, self.end.datetime if self.end is not None else None)

    def duration(self):
        return self.start.datetime(), self.end.datetime() if self.end is not None else self.end

    def combine_with(self, other):
        from timepiece.sections import sections
        if type(other) is FilterSpec:
            return RepeatAndFiltersSpec.using(repeat=self, filters=[other])
        elif type(other) is sections.IntervalSpec:
            return RepeatSpec.using(start=self.start, end=self.end, every=IntervalsSpec.contain(other))
        elif type(other) is IntervalsSpec:
            return RepeatSpec.using(start=self.start, end=self.end, every=other)
        else:
            super(RepeatSpec, self).or_with(other)

    def or_with(self, other):
        from timepiece.sections import sections
        one = RepeatAndFiltersSpec.using(repeat=self)
        if type(other) is RepeatSpec:
            two = RepeatAndFiltersSpec.using(repeat=other)
            return ManyRepeatAndFiltersSpec.using(specs=[one, two])
        elif type(other) is FilterSpec:
            two = RepeatAndFiltersSpec.using(repeat=self, filters=[other])
            return ManyRepeatAndFiltersSpec.using(specs=[one, other])
        elif type(other) is sections.IntervalSpec:
            two = RepeatAndFiltersSpec.using(
                  repeat = RepeatSpec.using(start=self.start, end=self.end, every=IntervalsSpec.contain(other))
                )
            return ManyRepeatAndFiltersSpec.using(specs=[one, two])
        elif type(other) is IntervalsSpec:
            two = RepeatAndFiltersSpec.using(
                  repeat = RepeatSpec.using(start=self.start, end=self.end, every=other)
                )
            return ManyRepeatAndFiltersSpec.using(specs=[one, two])
        else:
            super(RepeatSpec, self).or_with(other)

def gregorian_week(dt):
    """Thanks http://stackoverflow.com/a/32638267"""
    # The isocalendar week for this date
    iso_week = dt.isocalendar()[1]

    # The baseline Gregorian date for the beginning of our date's year
    base_greg = datetime.strptime('{0}-1-1'.format(dt.year), "%Y-%W-%w")

    # If the isocalendar week for this date is not 1, we need to
    # decrement the iso_week by 1 to get the Gregorian week number
    return iso_week if base_greg.isocalendar()[1] == 1 else iso_week - 1

class FilterSpec(BaseSpec):
    def __repr__(self):
        return "[{1}]".format(section_repr(self))
    specifies = ("filter", )
    minutes = dictobj.Field(lambda: ssv_spec(spec=sb.integer_spec()))
    hours = dictobj.Field(lambda: ssv_spec(spec=sb.integer_spec()))
    weeks = dictobj.Field(lambda: ssv_spec(spec=sb.integer_spec()))
    months = dictobj.Field(lambda: ssv_spec(spec=sb.integer_spec()))
    day_names = dictobj.Field(lambda: ssv_spec(weekday_names))
    day_numbers = dictobj.Field(lambda: ssv_spec(spec=sb.integer_spec()))

    def combine_with(self, other):
        if type(other) is DateTimeSpec:
            return RepeatAndFiltersSpec.using(repeat=RepeatSpec.using(start=other, filters=[self]))
        elif type(other) is RepeatSpec:
            return RepeatAndFiltersSpec.using(repeat=other, filters=[self]).simplify()
        elif type(other) is FilterSpec:
            kwargs = {}
            for field in self.fields:
                kwargs[field] = getattr(self, field) + getattr(other, field)
            return FilterSpec.using(**kwargs)
        elif type(other) is ManyRepeatAndFiltersSpec:
            new_specs = [RepeatAndFiltersSpec.uing(repeat=s.repeat, filters=s.filters + [self]) for s in other.specs]
            return ManyRepeatAndFiltersSpec(specs=new_specs)
        else:
            super(FilterSpec, self).combine_with(self, other)

    def is_filtered(self, at):
        filtered = True
        tup = at.timetuple()
        specified = lambda val: val not in (sb.NotSpecified, None)

        if specified(self.minutes) and tup.tm_min not in self.minutes:
            filtered = False
        if specified(self.hours) and tup.tm_hour not in self.hours:
            filtered = False
        if specified(self.weeks) and gregorian_week(at) not in self.weeks:
            filtered = False
        if specified(self.months) and tup.tm_mon not in self.months:
            filtered = False
        if specified(self.day_names) and weekday_names[tup.tm_wday] not in self.day_names:
            filtered = False
        if specified(self.day_numbers) and tup.tm_yday not in self.day_numbers:
            filtered = False

        return filtered

class RepeatAndFiltersSpec(BaseSpec):
    def __repr__(self):
        return "{0}{1}".format(repr(self.repeat), "".join(repr(f) for f in self.filters))
    specifies = ("repeat", "filter")
    repeat = dictobj.Field(lambda: fieldSpecs_from(RepeatSpec), wrapper=sb.required)
    filters = dictobj.Field(sb.listof(fieldSpecs_from(FilterSpec)))

    def following(self, at):
        return self.repeat.following(at)

    def is_filtered(self, at):
        return all(f.is_filtered(at) for f in self.filters)

    def simplify(self):
        return ManyRepeatAndFiltersSpec.using(specs=[self])

class ManyRepeatAndFiltersSpec(BaseSpec):
    def __repr__(self):
        return " | ".join(repr(rf) for rf in self.specs)
    specifies = ("repeat", "filter")
    specs = dictobj.Field(sb.listof(fieldSpecs_from(RepeatAndFiltersSpec)))

    def following(self, at=None):
        if at is None:
            at = datetime.utcnow()
        return min([rf.following(at) for rf in self.specs])

    def is_filtered(self, at):
        return any(rf.is_filtered(at) for rf in self.specs)

class DateTimeSpec(BaseSpec):
    __repr__ = section_repr
    _section_name = "Datetime"
    specifies = ("once", )
    datetime = dictobj.Field(sb.any_spec, wrapper=sb.required)

    @memoized_property
    def date(self):
        return self.datetime.date()

    @memoized_property
    def time(self):
        return self.datetime.time()

    @classmethod
    def contain(kls, dt):
        if isinstance(dt, float):
            dt = datetime.fromtimestamp(dt)
        return kls.FieldSpec().normalise(EmptyMeta, {"datetime": dt})

    def following(self, at=None):
        if at is None:
            at = datetime.utcnow()
        at = at.replace(microsecond=0)
        return None if at > self.datetime else self.datetime

    def is_filtered(self, at):
        if at < self.datetime:
            return False

        if at == self.datetime:
            return True

        if at - self.datetime < timedelta(seconds=30):
            return True

        return False

    def combine_with(self, other):
        from timepiece.sections import sections
        one = RepeatSpec.using(start=self)
        if type(other) is FilterSpec:
            return RepeatAndFiltersSpec.using(repeat=one, filters=[other])
        elif type(other) is sections.IntervalSpec:
            return RepeatSpec.using(start=self, every=IntervalsSpec.contain(other))
        elif type(other) is IntervalsSpec:
            return RepeatSpec.using(start=self, every=other)
        else:
            super(DateTimeSpec, self).or_with(other)

    def or_with(self, other):
        from timepiece.sections import sections
        repeat = RepeatSpec.using(start=self)
        one = RepeatAndFiltersSpec.using(repeat=repeat)
        if type(other) is RepeatSpec:
            two = RepeatAndFiltersSpec.using(repeat=other)
            return ManyRepeatAndFiltersSpec.using(specs=[one, two])
        elif type(other) is FilterSpec:
            two = RepeatAndFiltersSpec.using(repeat=repeat, filters=[other])
            return ManyRepeatAndFiltersSpec.using(specs=[one, other])
        elif type(other) is sections.IntervalSpec:
            two = RepeatAndFiltersSpec.using(
                  repeat = RepeatSpec.using(start=repeat.start, every=IntervalsSpec.contain(other))
                )
            return ManyRepeatAndFiltersSpec.using(specs=[one, two])
        elif type(other) is IntervalsSpec:
            two = RepeatAndFiltersSpec.using(
                  repeat = RepeatSpec.using(start=self, every=other)
                )
            return ManyRepeatAndFiltersSpec.using(specs=[one, two])
        else:
            super(DateTimeSpec, self).or_with(other)

def intervals_intervals_spec():
    from timepiece.sections import sections
    return sb.listof(fieldSpecs_from(sections.IntervalSpec))

class IntervalsSpec(BaseSpec):
    __repr__ = section_repr
    _section_name = "Intervals"
    specifies = ("interval", )
    intervals = dictobj.Field(intervals_intervals_spec)

    @classmethod
    def contain(kls, *intervals):
        return kls.FieldSpec().normalise(EmptyMeta, {"intervals": list(intervals)})

    def or_with(self, other):
        from timepiece.sections import sections
        if isinstance(other, IntervalsSpec):
            return IntervalsSpec.contain(*self.intervals, *other.intervals)
        elif isinstance(other, sections.IntervalSpec):
            return IntervalsSpec.contain(*self.intervals, other)
        return super(IntervalsSpec, self).or_with(other)

    def is_filtered(self, at):
        """Assume that this has been triggered because of using the following method, so don't reprocess"""
        return True

    def following(self, at, start, end):
        repeaters = []

        # Make a list of generators from our intervals
        for interval in self.intervals:
            repeaters.append(iter(interval.following(at, start, end)))

        # Keep generating a "round" of the next result from each repeater
        # Until:
        #
        #  * we have no valid values in a round
        #  * we have a value greater than `at`
        #  * we have attempted this over 100 times
        #
        round_count = -1
        while True:
            round_count += 1
            next_round = []

            # Fill out the next_round with valid values
            #
            # Where valid is:
            # * not None
            # * greater than start
            # * less or equal to end (minus microseconds)

            new_repeaters = []
            for repeater in repeaters:
                try:
                    nxt = next(repeater)
                except StopIteration:
                    pass
                else:
                    if nxt and nxt.replace(microsecond=0) <= end:
                        if nxt >= start and nxt >= at:
                            next_round.append(nxt)
                        new_repeaters.append(repeater)

            # Replace our repeaters with the ones that had valid values
            repeaters = new_repeaters

            # Quit if no more repeaters
            if not repeaters:
                break

            # No values this round, try again
            # i.e. all values were before the start date
            if not next_round:
                if round_count > 100:
                    break
                else:
                    continue

            # Find soonest following time
            mn = min(next_round)

            # Return the min if it's greater than our starting point
            if mn > at:
                return mn

            # Let's not spin forever and ever
            if round_count > 100:
                return mn

