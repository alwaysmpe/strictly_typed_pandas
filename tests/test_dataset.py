import pickle
import tempfile
from typing import ClassVar

import numpy as np  # type: ignore
import pandas as pd
import pytest

from strictly_typed_pandas import DataSet
from strictly_typed_pandas.pandas_types import StringDtype


class Schema:
    a: int
    b: str


class AlternativeSchema:
    a: int


class SchemaWithClassVar:
    a: int
    b: ClassVar[str] = "abc"


dictionary = {"a": [1, 2, 3], "b": ["a", "b", "c"]}


def test_empty_dataset() -> None:
    df = DataSet[Schema]()

    assert df.shape[0] == 0
    assert np.all(df.columns == ["a", "b"])

    assert df.dtypes.iloc[0] == int
    assert df.dtypes.iloc[1] == object or isinstance(df.dtypes.iloc[1], StringDtype)


def test_dataset() -> None:
    DataSet[Schema](dictionary)


def test_dataset_missing_colnames() -> None:
    with pytest.raises(TypeError):
        DataSet[Schema]({"a": []})


def test_dataset_too_many_colnames() -> None:
    with pytest.raises(TypeError):
        DataSet[Schema]({"a": [], "b": [], "c": []})


def test_dataset_check_types() -> None:
    with pytest.raises(TypeError):
        DataSet[Schema]({"a": ["1", "2", "3"], "b": ""})


def test_dataset_immutable() -> None:
    df = DataSet[Schema](dictionary)
    strings = ["1", "2", "3"]

    with pytest.raises(NotImplementedError):
        df["a"] = strings

    with pytest.raises(NotImplementedError):
        df.a = strings

    with pytest.raises(NotImplementedError):
        df.loc[:, "a"] = strings

    with pytest.raises(NotImplementedError):
        df.iloc[:, 0] = strings

    with pytest.raises(NotImplementedError):
        df.assign(a=strings, inplace=True)

    with pytest.raises(NotImplementedError):
        # 4th argument is inplace
        df.set_index(["a"], True, False, True)  # type: ignore

    assert isinstance(df.assign(a=strings), pd.DataFrame)


def test_dataset_to_dataframe() -> None:
    df = DataSet[Schema](dictionary)
    assert isinstance(df.to_dataframe(), pd.DataFrame)
    assert isinstance(df.to_frame(), pd.DataFrame)


def foo(df: DataSet[Schema]) -> DataSet[Schema]:
    return df


def test_typeguard_dataset() -> None:
    foo(DataSet[Schema]())

    with pytest.raises(TypeError):
        foo(DataSet[AlternativeSchema]())  # type: ignore

    with pytest.raises(TypeError):
        foo(pd.DataFrame())  # type: ignore


def test_duplicates() -> None:
    with pytest.raises(TypeError):
        DataSet[AlternativeSchema]([[1, 1]], columns=["a", "a"])


def test_pickle():
    df = DataSet[Schema](dictionary)

    with tempfile.TemporaryDirectory() as tmpdir:
        pickle.dump(df, open(f"{tmpdir}/test.pkl", "wb"))
        loaded = pickle.load(open(f"{tmpdir}/test.pkl", "rb"))

    assert (df == loaded).all().all()


def test_classvar_colum_not_allowed():
    with pytest.raises(TypeError):
        DataSet[SchemaWithClassVar](dictionary)


def test_classvar_colum_not_required():
    DataSet[SchemaWithClassVar]({"a": [1, 2, 3]})


class A:
    a: int


class B:
    a: int


def test_resetting_of_schema_annotations():
    df = DataSet[A]()

    a: pd.DataFrame

    # if no schema is specified, the annotation should be None
    a = DataSet(df)
    assert a._schema_annotations is None

    # when we specify a schema, the class variable will be set to A, but afterwards it should be
    # reset to None again when we initialize a new object without specifying a schema
    DataSet[A]
    a = DataSet(df)
    assert a._schema_annotations is None

    # and then to B
    a = DataSet[B](df)

    # and then to None again
    a = DataSet(df)
    assert a._schema_annotations is None
