import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np

# Données du benchmark
volumes = [500, 2000, 5000]

cass_write = [3.129, 13.167, 34.991]
pg_write   = [0.118,  0.832,  1.482]

cass_read  = [7.093, 19.746, 34.856]
pg_read    = [0.264,  1.484,  3.351]

# Agrégation
agg_labels  = ['Cassandra', 'PostgreSQL']
agg_times   = [257.97, 9.01]

plt.rcParams.update({
    'font.family': 'sans-serif',
    'font.size': 11,
    'axes.spines.top': False,
    'axes.spines.right': False,
})

fig, axes = plt.subplots(1, 3, figsize=(18, 6))
fig.suptitle(
    "Benchmark : Apache Cassandra (cluster 3 noeuds) vs PostgreSQL\n"
    "Systeme de surveillance meteo IoT — Douala",
    fontsize=13, fontweight='bold', y=1.02
)

x = np.arange(len(volumes))
width = 0.35
C = '#E05C5C'
P = '#2E86C1'

# Graphique 1 : Écriture
ax1 = axes[0]
ax1.set_facecolor('#FAFAFA')
b1 = ax1.bar(x - width/2, cass_write, width, label='Cassandra', color=C, alpha=0.85)
b2 = ax1.bar(x + width/2, pg_write,   width, label='PostgreSQL', color=P, alpha=0.85)
ax1.set_title("Temps d'ecriture (s)", fontweight='bold', fontsize=11)
ax1.set_xlabel("Nombre d'operations")
ax1.set_ylabel("Temps (s)")
ax1.set_xticks(x)
ax1.set_xticklabels(volumes)
ax1.legend()
for bar in b1:
    ax1.text(bar.get_x()+bar.get_width()/2, bar.get_height()+0.3,
             f'{bar.get_height():.2f}s', ha='center', va='bottom',
             fontsize=8, color=C, fontweight='bold')
for bar in b2:
    ax1.text(bar.get_x()+bar.get_width()/2, bar.get_height()+0.3,
             f'{bar.get_height():.2f}s', ha='center', va='bottom',
             fontsize=8, color=P, fontweight='bold')

# Graphique 2 : Lecture
ax2 = axes[1]
ax2.set_facecolor('#FAFAFA')
b3 = ax2.bar(x - width/2, cass_read, width, label='Cassandra', color=C, alpha=0.85)
b4 = ax2.bar(x + width/2, pg_read,   width, label='PostgreSQL', color=P, alpha=0.85)
ax2.set_title("Temps de lecture (s)", fontweight='bold', fontsize=11)
ax2.set_xlabel("Nombre d'operations")
ax2.set_ylabel("Temps (s)")
ax2.set_xticks(x)
ax2.set_xticklabels(volumes)
ax2.legend()
for bar in b3:
    ax2.text(bar.get_x()+bar.get_width()/2, bar.get_height()+0.3,
             f'{bar.get_height():.2f}s', ha='center', va='bottom',
             fontsize=8, color=C, fontweight='bold')
for bar in b4:
    ax2.text(bar.get_x()+bar.get_width()/2, bar.get_height()+0.3,
             f'{bar.get_height():.2f}s', ha='center', va='bottom',
             fontsize=8, color=P, fontweight='bold')

# Graphique 3 : Ratio performance
ax3 = axes[2]
ax3.set_facecolor('#FAFAFA')
ratios_write = [c/p for c, p in zip(cass_write, pg_write)]
ratios_read  = [c/p for c, p in zip(cass_read,  pg_read)]
x2 = np.arange(len(volumes))
bw = ax3.bar(x2 - width/2, ratios_write, width, label='Ecriture', color='#E67E22', alpha=0.85)
br = ax3.bar(x2 + width/2, ratios_read,  width, label='Lecture',  color='#8E44AD', alpha=0.85)
ax3.axhline(y=1, color='gray', linestyle='--', alpha=0.5, label='Egalite')
ax3.set_title("Ratio Cassandra/PostgreSQL\n(>1 = PostgreSQL plus rapide)", fontweight='bold', fontsize=10)
ax3.set_xlabel("Nombre d'operations")
ax3.set_ylabel("Ratio (x fois)")
ax3.set_xticks(x2)
ax3.set_xticklabels(volumes)
ax3.legend()
for bar in bw:
    ax3.text(bar.get_x()+bar.get_width()/2, bar.get_height()+0.1,
             f'{bar.get_height():.1f}x', ha='center', va='bottom',
             fontsize=8, color='#E67E22', fontweight='bold')
for bar in br:
    ax3.text(bar.get_x()+bar.get_width()/2, bar.get_height()+0.1,
             f'{bar.get_height():.1f}x', ha='center', va='bottom',
             fontsize=8, color='#8E44AD', fontweight='bold')

# Note
fig.text(0.5, -0.05,
    "Note : Cassandra tourne sur un cluster distribue 3 noeuds (Docker) avec ConsistencyLevel.QUORUM.\n"
    "PostgreSQL tourne en instance unique locale. Les performances Cassandra s'ameliorent avec plus de noeuds et de donnees.",
    ha='center', fontsize=9, style='italic', color='gray')

plt.tight_layout()
plt.savefig('benchmark/resultats_benchmark_pg.png', dpi=150, bbox_inches='tight')
print("Graphique sauvegarde : benchmark/resultats_benchmark_pg.png", flush=True)
plt.show()
