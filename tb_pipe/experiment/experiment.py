import logging
from logging import getLogger
from typing import Optional, Callable

import numpy as np
import pandas as pd
from category_encoders.utils import convert_input, convert_input_vector
from sklearn.utils.validation import indexable

from ..typing_template import TYPE_DATASET, TYPE_CV
from ..validation.cross_validate import Trainer


def run(trainer: Trainer,
        train: TYPE_DATASET,
        test: Optional[TYPE_DATASET] = None,
        target: Optional[TYPE_DATASET] = None,
        scoring: Optional[Callable] = None,
        cv: TYPE_CV = None,
        groups: Optional[pd.Series] = None,
        logger: Optional[logging.RootLogger] = None):
    if logger is None:
        logger = getLogger(__name__)
    train, target, groups = indexable(train, target, groups)

    train = convert_input(train)
    target = convert_input_vector(target, train.index)
    predictions = None
    if test is not None:
        test = convert_input(test)
        predictions = np.zeros(len(test))
    oof = np.zeros(len(train))

    feature_importance = []
    scores = []
    for idx, (trn_idx, val_idx) in enumerate(cv.split(train, target, groups)):
        logger.info('Fold: {}/{}'.format(idx + 1, cv.n_splits))
        logger.info(
            'Length train: {} / valid: {}'.format(len(trn_idx), len(val_idx)))
        train_x, train_y = train.iloc[trn_idx], target.iloc[trn_idx]
        valid_x, valid_y = train.iloc[val_idx], target.iloc[val_idx]

        trainer.train(train_x, train_y)

        oof[val_idx] = trainer.predict(valid_x)
        if test is not None:
            predictions += trainer.predict(test)
        if scoring is not None:
            score = scoring(valid_y, oof[val_idx])
            logger.info("Fold {} Score: {}".format(idx, score))
            scores.append(score)
        feature_importance.append(trainer.get_feature_importance())

    if scoring is not None:
        score = scoring(target, oof)
        logger.info("Overall Score: {}".format(score))

    prediction = None
    if test is not None:
        prediction = predictions / cv.get_n_splits(train, target, groups)

    return oof, prediction, feature_importance
