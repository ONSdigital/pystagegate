import pandas as pd

from pystagegate.functions import filler


def test_filler():
    df = pd.DataFrame()

    pd.testing.assert_frame_equal(df, filler(df))
