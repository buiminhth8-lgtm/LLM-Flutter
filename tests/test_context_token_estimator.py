from llm_studio.context.estimators import TokenEstimator


def test_token_estimator_is_stable_for_chinese_english_and_mixed_text():
    estimator = TokenEstimator()

    assert estimator.estimate("这是中文文本。") == estimator.estimate("这是中文文本。")
    assert estimator.estimate("这是中文文本。") > 0
    assert estimator.estimate("stable English words") > 0
    assert estimator.estimate("中文 and English 123.") > 0
    assert estimator.estimate("") == 0
