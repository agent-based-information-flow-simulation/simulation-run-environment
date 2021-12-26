import numpy as np


def bilinear(s1, s2, m1, m2, fQ11, fQ12, fQ21, fQ22):
    A = np.array(
        [
            [1, 1, 1, 1],
            [s1, s1, s2, s2],
            [m1, m2, m1, m2],
            [s1 * m1, s1 * m2, s2 * m1, s2 * m2],
        ]
    )
    A = np.transpose(A)

    B = np.array([fQ11, fQ12, fQ21, fQ22])
    return np.linalg.solve(A, B)


def calculate_accept(msg_power, susceptibility, coefs=[-15.333, 0.817, 0.02, 0.004]):
    """Function to calulate the probability of accepting the news

    Default values for coefficients have been taken by using
    the bilinear function with the following values:
    s1 = 20
    s2 = 80
    m1 = 0
    m2 = 100
    fQ11 = 1
    fQ12 = 10
    fQ21 = 50
    fQ22 = 80
    """
    return (
        coefs[0]
        + coefs[1] * susceptibility
        + coefs[2] * msg_power
        + coefs[3] * msg_power * susceptibility
    )
