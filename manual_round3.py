import numpy as np
mult = np.array([[24, 70, 41, 21, 60], [47, 82, 87, 80, 35], [73, 89, 100, 90, 17], [77, 83, 85, 79, 55], [12, 27, 52, 15, 30]])
hunt = np.array([[2, 4, 3, 2, 4], [3, 5, 5, 5, 3], [4 , 5 , 8 + 5, 7 + 5, 2], [5, 5, 5, 5, 4], [2, 3, 4, 2, 3]])
players = np.ones((5, 5))*100/25
total_hunters = hunt + players
distr = mult/total_hunters
print(distr)

for k in range(1):
    for i in range(5):
        for j in range(5):
            if distr[i][j] > 10:
                players[i][j] += 1
            else:
                players[i][j] = 0
    players[np.where(players == 0)] = (60 - np.sum(players))/(np.sum(players == 0))
    total_hunters = hunt + players
    distr = mult/total_hunters
    print(distr)
