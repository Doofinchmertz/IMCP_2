matrix = [[1, 0.48, 1.52, 0.71], [2.05, 1, 3.26, 1.56], [0.64, 0.3, 1, 0.46], [1.41, 0.61, 2.08, 1]]

# pizza slice -> 0
# wasabi -> 1
# snowball -> 2
# shell -> 3

max_final = -1
max_final_at = [3, -1, -1, -1, -1, 3]

initial = 1

a = 3
f = 3
for b in range(4):
    for c in range(4):
        for d in range(4):
            for e in range(4):
                final = initial*matrix[a][b]*matrix[b][c]*matrix[c][d]*matrix[d][e]*matrix[e][f]
                if final > max_final:
                    max_final_at = [a, b, c, d, e, f]
                    max_final = final

print(max_final_at)
print(max_final)