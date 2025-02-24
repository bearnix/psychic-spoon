import numpy as np
import scipy.stats as stats
import seaborn as sns
import matplotlib.pyplot as plt

def generate_samples(distribution, size, **kwargs):
    """Genererar slumpmässiga samples från en given fördelning."""
    if distribution == 'normal':
        return np.random.normal(kwargs.get('loc', 0), kwargs.get('scale', 1), size)
    elif distribution == 'uniform':
        return np.random.uniform(kwargs.get('low', -1), kwargs.get('high', 1), size)
    elif distribution == 'triangular':
        return np.random.triangular(kwargs.get('left', -1), kwargs.get('mode', 0), kwargs.get('right', 1), size)
    elif distribution == 'half_triangular':
        return np.random.triangular(kwargs.get('left', -1), kwargs.get('mode', 1), kwargs.get('right', 1), size)
    elif distribution == 'weibull':
        return np.random.weibull(kwargs.get('shape', 2), size)
    else:
        raise ValueError("Ogiltig fördelningstyp")

def bimodial_dist(p1, p2, **kwargs):
    p1=float(p1)
    p2=float(p2)
    if np.random.uniform() > (p2/(p1+p2)): # p1
        return np.random.normal(kwargs.get('loc', 2.5), kwargs.get('scale', 1), 1)
    else: #p2
        return np.random.normal(kwargs.get('loc', 0), kwargs.get('scale', 1), 1)

def plot_sampling_distribution(distribution, sample_sizes, num_samples, **kwargs):
    """Plottar samplingarnas medelvärdesfördelning."""
    plt.figure(figsize=(15, 5))
    
    for i, n in enumerate(sample_sizes, 1):
        means = [np.mean(generate_samples(distribution, n, **kwargs)) for _ in range(num_samples)]
        plt.subplot(1, len(sample_sizes), i)
        sns.histplot(means, kde=True, bins=20)
        plt.title(f'{distribution.capitalize()} - n={n}')
        print(stats.shapiro(means))
    
    plt.show()

# Parameterinställningar
np.random.seed(42)
sample_sizes = [10, 20, 30]
num_samples = 100

# Plotta samplingarnas medelvärdesfördelning
for dist in ['normal', 'uniform', 'triangular']:
    plot_sampling_distribution(dist, sample_sizes, num_samples)
