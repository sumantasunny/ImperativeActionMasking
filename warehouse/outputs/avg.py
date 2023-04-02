import numpy as np
import matplotlib.pyplot as plt
import sys

y = []
diff = int(sys.argv[1]) # Last terms to eliminate (1 term)
layout = sys.argv[2]
score_range = int(sys.argv[3])

for i in range(score_range+1):
    file_name = "scores_"+layout+"_b0_w0_ls1_la"+str(i)+"_n320_x0_y300.txt"
    # file_name = "wins_"+layout+"_b0_w0_ls1_la"+str(i)+"_n320_x0_y300.txt"
    with open(file_name) as f:
        lines = f.readlines()
        w = []
        for line in lines:
            w.append(float(line))
        avg = 0
        if diff > 0:
            avg = sum(w[:-diff])/len(w[:-diff])
        else:
            avg = sum(w)/len(w)
        print(avg)
        y.append(avg)
        
x = range(score_range+1)

fig = plt.figure()
ax = fig.add_subplot(1, 1, 1)

plt.plot(x, y, 
         marker='o', color='b')

plt.title("Pacman's Training Score using Look Ahead Shield")
# plt.title("Pacman's Winning Rate using Look Ahead Shield")
plt.ylabel("Average Rewards")
# plt.ylabel("Winning Rate")
plt.xlabel("Look Ahead")
# plt.legend()
# plt.legend(bbox_to_anchor=(1.0, 1.3), loc='upper left')
plt.tight_layout()
x_major_ticks = np.array(range(score_range//2 + 1))*2
ax.set_xticks(x_major_ticks)
# y_major_ticks = np.array(range(score_range//2 + 1))/10
# ax.set_yticks(y_major_ticks)
plt.grid()
plt.savefig("../plots/lookAhead_"+layout+".png")   # save the figure to file
plt.show()