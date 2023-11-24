from collections.abc import Iterable
from hdmf.common import VectorData
from hdmf.utils import docval, getargs, get_docval, popargs
from pynwb import register_class
from pynwb.file import LabMetaData


@register_class('HedAnnotations', 'ndx-hed')
class HedAnnotations(VectorData):
    """
    Column storing HED (Hierarchical Event Descriptors) annotations for a row. A HED string is a comma-separated,
    and possibly parenthesized list of HED tags selected from a valid HED vocabulary as specified by the
    NWBFile field HEDVersion.

    """

    __nwbfields__ = ('name', 'description', 'hed_strings')

    @docval({'name': 'description', 'type': str,
             'doc': 'Column name indicating that this column is of type HedAnnotations',
             'default': "Column name indicating that this column is of type HedAnnotations"},
            {'name': 'hed_strings', 'type': Iterable, 'shape': (None, ),  # required
             'doc': 'HED strings of type str.'}, *get_docval(VectorData.__init__, 'data'))
    def __init__(self, **kwargs):
        description, hed_strings = popargs('description', 'hed_strings', kwargs)
        super().__init__(**kwargs)
        self.name = 'HED'
        self.description = description
        self.hed_strings = hed_strings
        # CAUTION: Define any logic specific for init in the self._init_internal function, not here!
        # TODO: How is the HEDSchema object going to be stored as we do not want to recreate?
        self._init_internal()

    def _init_internal(self):
        """
        #TODO:  check the validity of hed_strings.   Where is the HEDSchema going to come from?
        """
        pass

    @docval({'name': 'val', 'type': str,
             'doc': 'the value to add to this column. Should be a valid HED string.'})
    def add_row(self, **kwargs):
        """Append a data value to this column."""
        val = kwargs['val']
        val.check_types()
        # TODO how to validate
        super().append(val)

    @docval({'name': 'arg', 'type': str,
             'doc': 'the value to append to this column. Should be a valid HED string.'})
    def append(self, **kwargs):
        """Append a data value to this column."""
        # this is the same as add_row?
        arg = kwargs['arg']
        arg.check_types()
        super().append(arg)

    def get(self, key, **kwargs):
        """
        Retrieve elements from this object.

        """
        # The function uses :py:class:`~pynwb.base.TimeSeriesReferenceVectorData.TIME_SERIES_REFERENCE_TUPLE`
        # to describe individual records in the dataset. This allows the code to avoid exposing internal
        # details of the schema to the user and simplifies handling of missing values by explicitly
        # representing missing values via
        # :py:class:`~pynwb.base.TimeSeriesReferenceVectorData.TIME_SERIES_REFERENCE_NONE_TYPE`
        # rather than the internal representation used for storage of ``(-1, -1, TimeSeries)``.
        #
        # :param key: Selection of the elements
        # :param kwargs: Ignored
        #
        # :returns: :py:class:`~pynwb.base.TimeSeriesReferenceVectorData.TIME_SERIES_REFERENCE_TUPLE` if a single
        #           element is being selected. Otherwise return a list of
        #           :py:class:`~pynwb.base.TimeSeriesReferenceVectorData.TIME_SERIES_REFERENCE_TUPLE` objects.
        #           Missing values are represented by
        #           :py:class:`~pynwb.base.TimeSeriesReferenceVectorData.TIME_SERIES_REFERENCE_NONE_TYPE`
        #           in which all values (i.e., idx_start, count, timeseries) are set to None.
        # """
        # TODO: We need to add capability of getting a slice as in TimeSeriesReferenceVectorData
        vals = super().get(key)
        return vals
        # # we only selected one row.
        # if isinstance(key, (int, np.integer)):
        #     # NOTE: If we never wrote the data to disk, then vals will be a single tuple.
        #     #       If the data is loaded from an h5py.Dataset then vals will be a single
        #     #       np.void object. I.e., an alternative check would be
        #     #       if isinstance(vals, tuple) or isinstance(vals, np.void):
        #     #          ...
        #     if vals[0] < 0 or vals[1] < 0:
        #         return self.TIME_SERIES_REFERENCE_NONE_TYPE
        #     else:
        #         return self.TIME_SERIES_REFERENCE_TUPLE(*vals)
        # else:  # key selected multiple rows
        #     # When loading from HDF5 we get an np.ndarray otherwise we get list-of-list. This
        #     # makes the values consistent and transforms the data to use our namedtuple type
        #     re = [self.TIME_SERIES_REFERENCE_NONE_TYPE
        #           if (v[0] < 0 or v[1] < 0) else self.TIME_SERIES_REFERENCE_TUPLE(*v)
        #           for v in vals]
        #     return re

    @docval({'name': 'val', 'type': 'str', 'doc': 'the value to add to this column'})
    def add_row(self, **kwargs):
        """Append a HED annotation to this VectorData column"""
        val = getargs('val', kwargs)
        if val is not None and self.validate(val):
            if self.term_set.validate(term=val):
                self.append(val)
            else:
                msg = ("%s is not in the term set." % val)
                raise ValueError(msg)

        else:
            self.append(val)

    @docval({'name': 'val', 'type': 'str', 'doc': 'the value to validate'})
    def validate(self, **kwargs):
        """Validate this HED string"""
        val = getargs('val', kwargs)
        return True


@register_class("HedVersion", "ndx-hed")
class HedVersion(LabMetaData):
    """
    Column storing HED (Hierarchical Event Descriptors) annotations for a row. A HED string is a comma-separated,
    and possibly parenthesized list of HED tags selected from a valid HED vocabulary as specified by the
    NWBFile field HEDVersion.

    """

    __nwbfields__ = ('name', 'description', 'hed_version', 'hed_schemas')

    @docval({'name': 'description', 'type': str,
             'doc': 'Column name indicating that this column is of type HedAnnotations',
             'default': "Column name indicating that this column is of type HedAnnotations"},
            {'name': 'hed_version', 'type': 'array_data',  'doc': 'HED strings of type str', 'shape': (None,)})
    def __init__(self, **kwargs):
        description, hed_strings = popargs('description', 'hed_strings', kwargs)
        kwargs['name'] = 'HED'
        super().__init__(**kwargs)
        self.description = description
        self.hed_strings = hed_strings
        # CAUTION: Define any logic specific for init in the self._init_internal function, not here!
        # TODO: How is the HEDSchema object going to be stored as we do not want to recreate?
        self._init_internal()

    def _init_internal(self):
        """
        #TODO:  check the validity of hed_strings.   Where is the HEDSchema going to come from?
        """
        pass
