import numpy as np
from src.evaluate import confusion_matrix, miou
from src.change_analysis import transition_matrix, class_summary


def test_perfect_prediction_gives_miou_1():
    m = np.array([[0, 1], [2, 1]])
    assert miou(confusion_matrix(m, m, 3)) == 1.0


def test_transition_matrix_area():
    a = np.array([[0, 0], [1, 1]])
    b = np.array([[0, 1], [1, 1]])
    tm = transition_matrix(a, b, 2, pixel_area_ha=1)
    assert tm[0, 1] == 1 and tm[0, 0] == 1 and tm[1, 1] == 2
    assert class_summary(tm, 4)["net_change"].tolist() == [-1, 1]
