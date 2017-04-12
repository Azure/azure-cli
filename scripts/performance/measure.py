# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import sys
from subprocess import check_output, STDOUT

def mean(data):
    """Return the sample arithmetic mean of data."""
    n = len(data)
    if n < 1:
        raise ValueError('len < 1')
    return sum(data)/float(n)


def sq_deviation(data):
    """Return sum of square deviations of sequence data."""
    c = mean(data)
    return sum((x-c)**2 for x in data)


def pstdev(data):
    """Calculates the population standard deviation."""
    n = len(data)
    if n < 2:
        raise ValueError('len < 2')
    ss = sq_deviation(data)
    return (ss/n) ** 0.5


real = []
user = []
syst = []
loop = 100

for i in range(loop):
    lines = check_output(['time -p az'], shell=True, stderr=STDOUT).split('\n')
    real_time = float(lines[-4].split()[1])
    real.append(float(lines[-4].split()[1]))
    user.append(float(lines[-3].split()[1]))
    syst.append(float(lines[-2].split()[1]))
    sys.stdout.write('Loop {} => {} \n'.format(i, real_time))
    sys.stdout.flush()

print('Real: mean => {} \t pstdev => {}'.format(mean(real), pstdev(real)))
print('User: mean => {} \t pstdev => {}'.format(mean(user), pstdev(user)))
print('Syst: mean => {} \t pstdev => {}'.format(mean(syst), pstdev(syst)))
