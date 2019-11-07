import random

import numpy as np
import pytest

from pandas import Categorical, DataFrame, IntervalIndex, MultiIndex, Series
import pandas.util.testing as tm


class TestSeriesSorting:
    def test_sort_values(self, datetime_series):

        # check indexes are reordered corresponding with the values
        ser = Series([3, 2, 4, 1], ["A", "B", "C", "D"])
        expected = Series([1, 2, 3, 4], ["D", "B", "A", "C"])
        result = ser.sort_values()
        tm.assert_series_equal(expected, result)

        ts = datetime_series.copy()
        ts[:5] = np.NaN
        vals = ts.values

        result = ts.sort_values()
        assert np.isnan(result[-5:]).all()
        tm.assert_numpy_array_equal(result[:-5].values, np.sort(vals[5:]))

        # na_position
        result = ts.sort_values(na_position="first")
        assert np.isnan(result[:5]).all()
        tm.assert_numpy_array_equal(result[5:].values, np.sort(vals[5:]))

        # something object-type
        ser = Series(["A", "B"], [1, 2])
        # no failure
        ser.sort_values()

        # ascending=False
        ordered = ts.sort_values(ascending=False)
        expected = np.sort(ts.dropna().values)[::-1]
        tm.assert_almost_equal(expected, ordered.dropna().values)
        ordered = ts.sort_values(ascending=False, na_position="first")
        tm.assert_almost_equal(expected, ordered.dropna().values)

        # ascending=[False] should behave the same as ascending=False
        ordered = ts.sort_values(ascending=[False])
        expected = ts.sort_values(ascending=False)
        tm.assert_series_equal(expected, ordered)
        ordered = ts.sort_values(ascending=[False], na_position="first")
        expected = ts.sort_values(ascending=False, na_position="first")
        tm.assert_series_equal(expected, ordered)

        msg = "ascending must be boolean"
        with pytest.raises(ValueError, match=msg):
            ts.sort_values(ascending=None)
        msg = r"Length of ascending \(0\) must be 1 for Series"
        with pytest.raises(ValueError, match=msg):
            ts.sort_values(ascending=[])
        msg = r"Length of ascending \(3\) must be 1 for Series"
        with pytest.raises(ValueError, match=msg):
            ts.sort_values(ascending=[1, 2, 3])
        msg = r"Length of ascending \(2\) must be 1 for Series"
        with pytest.raises(ValueError, match=msg):
            ts.sort_values(ascending=[False, False])
        msg = "ascending must be boolean"
        with pytest.raises(ValueError, match=msg):
            ts.sort_values(ascending="foobar")

        # inplace=True
        ts = datetime_series.copy()
        ts.sort_values(ascending=False, inplace=True)
        tm.assert_series_equal(ts, datetime_series.sort_values(ascending=False))
        tm.assert_index_equal(
            ts.index, datetime_series.sort_values(ascending=False).index
        )

        # GH 5856/5853
        # Series.sort_values operating on a view
        df = DataFrame(np.random.randn(10, 4))
        s = df.iloc[:, 0]

        msg = (
            "This Series is a view of some other array, to sort in-place"
            " you must create a copy"
        )
        with pytest.raises(ValueError, match=msg):
            s.sort_values(inplace=True)

    def test_sort_index(self, datetime_series):
        rindex = list(datetime_series.index)
        random.shuffle(rindex)

        random_order = datetime_series.reindex(rindex)
        sorted_series = random_order.sort_index()
        tm.assert_series_equal(sorted_series, datetime_series)

        # descending
        sorted_series = random_order.sort_index(ascending=False)
        tm.assert_series_equal(
            sorted_series, datetime_series.reindex(datetime_series.index[::-1])
        )

        # compat on level
        sorted_series = random_order.sort_index(level=0)
        tm.assert_series_equal(sorted_series, datetime_series)

        # compat on axis
        sorted_series = random_order.sort_index(axis=0)
        tm.assert_series_equal(sorted_series, datetime_series)

        msg = "No axis named 1 for object type <class 'pandas.core.series.Series'>"
        with pytest.raises(ValueError, match=msg):
            random_order.sort_values(axis=1)

        sorted_series = random_order.sort_index(level=0, axis=0)
        tm.assert_series_equal(sorted_series, datetime_series)

        with pytest.raises(ValueError, match=msg):
            random_order.sort_index(level=0, axis=1)

    def test_sort_index_inplace(self, datetime_series):

        # For #11402
        rindex = list(datetime_series.index)
        random.shuffle(rindex)

        # descending
        random_order = datetime_series.reindex(rindex)
        result = random_order.sort_index(ascending=False, inplace=True)

        assert result is None
        tm.assert_series_equal(
            random_order, datetime_series.reindex(datetime_series.index[::-1])
        )

        # ascending
        random_order = datetime_series.reindex(rindex)
        result = random_order.sort_index(ascending=True, inplace=True)

        assert result is None
        tm.assert_series_equal(random_order, datetime_series)

    @pytest.mark.parametrize("level", ["A", 0])  # GH 21052
    def test_sort_index_multiindex(self, level):

        mi = MultiIndex.from_tuples([[1, 1, 3], [1, 1, 1]], names=list("ABC"))
        s = Series([1, 2], mi)
        backwards = s.iloc[[1, 0]]

        # implicit sort_remaining=True
        res = s.sort_index(level=level)
        tm.assert_series_equal(backwards, res)

        # GH13496
        # sort has no effect without remaining lvls
        res = s.sort_index(level=level, sort_remaining=False)
        tm.assert_series_equal(s, res)

    def test_sort_index_kind(self):
        # GH #14444 & #13589:  Add support for sort algo choosing
        series = Series(index=[3, 2, 1, 4, 3])
        expected_series = Series(index=[1, 2, 3, 3, 4])

        index_sorted_series = series.sort_index(kind="mergesort")
        tm.assert_series_equal(expected_series, index_sorted_series)

        index_sorted_series = series.sort_index(kind="quicksort")
        tm.assert_series_equal(expected_series, index_sorted_series)

        index_sorted_series = series.sort_index(kind="heapsort")
        tm.assert_series_equal(expected_series, index_sorted_series)

    def test_sort_index_na_position(self):
        series = Series(index=[3, 2, 1, 4, 3, np.nan])

        expected_series_first = Series(index=[np.nan, 1, 2, 3, 3, 4])
        index_sorted_series = series.sort_index(na_position="first")
        tm.assert_series_equal(expected_series_first, index_sorted_series)

        expected_series_last = Series(index=[1, 2, 3, 3, 4, np.nan])
        index_sorted_series = series.sort_index(na_position="last")
        tm.assert_series_equal(expected_series_last, index_sorted_series)

    def test_sort_index_intervals(self):
        s = Series(
            [np.nan, 1, 2, 3], IntervalIndex.from_arrays([0, 1, 2, 3], [1, 2, 3, 4])
        )

        result = s.sort_index()
        expected = s
        tm.assert_series_equal(result, expected)

        result = s.sort_index(ascending=False)
        expected = Series(
            [3, 2, 1, np.nan], IntervalIndex.from_arrays([3, 2, 1, 0], [4, 3, 2, 1])
        )
        tm.assert_series_equal(result, expected)

    def test_sort_values_categorical(self):

        c = Categorical(["a", "b", "b", "a"], ordered=False)
        cat = Series(c.copy())

        # sort in the categories order
        expected = Series(
            Categorical(["a", "a", "b", "b"], ordered=False), index=[0, 3, 1, 2]
        )
        result = cat.sort_values()
        tm.assert_series_equal(result, expected)

        cat = Series(Categorical(["a", "c", "b", "d"], ordered=True))
        res = cat.sort_values()
        exp = np.array(["a", "b", "c", "d"], dtype=np.object_)
        tm.assert_numpy_array_equal(res.__array__(), exp)

        cat = Series(
            Categorical(
                ["a", "c", "b", "d"], categories=["a", "b", "c", "d"], ordered=True
            )
        )
        res = cat.sort_values()
        exp = np.array(["a", "b", "c", "d"], dtype=np.object_)
        tm.assert_numpy_array_equal(res.__array__(), exp)

        res = cat.sort_values(ascending=False)
        exp = np.array(["d", "c", "b", "a"], dtype=np.object_)
        tm.assert_numpy_array_equal(res.__array__(), exp)

        raw_cat1 = Categorical(
            ["a", "b", "c", "d"], categories=["a", "b", "c", "d"], ordered=False
        )
        raw_cat2 = Categorical(
            ["a", "b", "c", "d"], categories=["d", "c", "b", "a"], ordered=True
        )
        s = ["a", "b", "c", "d"]
        df = DataFrame(
            {"unsort": raw_cat1, "sort": raw_cat2, "string": s, "values": [1, 2, 3, 4]}
        )

        # Cats must be sorted in a dataframe
        res = df.sort_values(by=["string"], ascending=False)
        exp = np.array(["d", "c", "b", "a"], dtype=np.object_)
        tm.assert_numpy_array_equal(res["sort"].values.__array__(), exp)
        assert res["sort"].dtype == "category"

        res = df.sort_values(by=["sort"], ascending=False)
        exp = df.sort_values(by=["string"], ascending=True)
        tm.assert_series_equal(res["values"], exp["values"])
        assert res["sort"].dtype == "category"
        assert res["unsort"].dtype == "category"

        # unordered cat, but we allow this
        df.sort_values(by=["unsort"], ascending=False)

        # multi-columns sort
        # GH 7848
        df = DataFrame(
            {"id": [6, 5, 4, 3, 2, 1], "raw_grade": ["a", "b", "b", "a", "a", "e"]}
        )
        df["grade"] = Categorical(df["raw_grade"], ordered=True)
        df["grade"] = df["grade"].cat.set_categories(["b", "e", "a"])

        # sorts 'grade' according to the order of the categories
        result = df.sort_values(by=["grade"])
        expected = df.iloc[[1, 2, 5, 0, 3, 4]]
        tm.assert_frame_equal(result, expected)

        # multi
        result = df.sort_values(by=["grade", "id"])
        expected = df.iloc[[2, 1, 5, 4, 3, 0]]
        tm.assert_frame_equal(result, expected)
