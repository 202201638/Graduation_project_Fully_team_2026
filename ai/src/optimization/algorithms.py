import math
import random
from dataclasses import dataclass
from typing import Callable, Dict, List, Tuple


ObjectiveFn = Callable[[Dict[str, float]], float]


@dataclass
class SearchDimension:
    name: str
    low: float
    high: float
    cast: str = "float"  # float | int

    def sample(self) -> float:
        return random.uniform(self.low, self.high)

    def clip(self, value: float):
        v = max(self.low, min(self.high, value))
        if self.cast == "int":
            return int(round(v))
        return float(v)


def _vector_to_params(vector: List[float], dims: List[SearchDimension]) -> Dict[str, float]:
    return {d.name: d.clip(v) for d, v in zip(dims, vector)}


def _random_vector(dims: List[SearchDimension]) -> List[float]:
    return [d.sample() for d in dims]


def _score_candidate(
    vector: List[float],
    dims: List[SearchDimension],
    objective: ObjectiveFn,
) -> Tuple[float, Dict[str, float]]:
    params = _vector_to_params(vector, dims)
    # We maximize validation performance.
    score = objective(params)
    return score, params


def pso_optimize(
    objective: ObjectiveFn,
    dims: List[SearchDimension],
    population: int = 8,
    iterations: int = 4,
):
    particles = [_random_vector(dims) for _ in range(population)]
    velocities = [[0.0 for _ in dims] for _ in range(population)]
    pbest = [p[:] for p in particles]
    pbest_score = [-1e18] * population
    gbest = particles[0][:]
    gbest_score = -1e18
    gbest_params: Dict[str, float] = {}

    w, c1, c2 = 0.7, 1.4, 1.4
    for _ in range(iterations):
        for i, part in enumerate(particles):
            score, params = _score_candidate(part, dims, objective)
            if score > pbest_score[i]:
                pbest_score[i] = score
                pbest[i] = part[:]
            if score > gbest_score:
                gbest_score = score
                gbest = part[:]
                gbest_params = params
        for i in range(population):
            for j in range(len(dims)):
                r1 = random.random()
                r2 = random.random()
                velocities[i][j] = (
                    w * velocities[i][j]
                    + c1 * r1 * (pbest[i][j] - particles[i][j])
                    + c2 * r2 * (gbest[j] - particles[i][j])
                )
                particles[i][j] += velocities[i][j]
    return gbest_params, gbest_score


def gwo_optimize(objective: ObjectiveFn, dims: List[SearchDimension], population: int = 8, iterations: int = 4):
    wolves = [_random_vector(dims) for _ in range(population)]
    alpha, beta, delta = wolves[0][:], wolves[0][:], wolves[0][:]
    alpha_s, beta_s, delta_s = -1e18, -1e18, -1e18
    best_params: Dict[str, float] = {}

    for t in range(iterations):
        for wv in wolves:
            s, p = _score_candidate(wv, dims, objective)
            if s > alpha_s:
                delta_s, delta = beta_s, beta[:]
                beta_s, beta = alpha_s, alpha[:]
                alpha_s, alpha = s, wv[:]
                best_params = p
            elif s > beta_s:
                delta_s, delta = beta_s, beta[:]
                beta_s, beta = s, wv[:]
            elif s > delta_s:
                delta_s, delta = s, wv[:]

        a = 2 - (2 * t / max(1, iterations - 1))
        for i in range(population):
            for j in range(len(dims)):
                r1, r2 = random.random(), random.random()
                a1 = 2 * a * r1 - a
                c1 = 2 * r2
                d_alpha = abs(c1 * alpha[j] - wolves[i][j])
                x1 = alpha[j] - a1 * d_alpha

                r1, r2 = random.random(), random.random()
                a2 = 2 * a * r1 - a
                c2 = 2 * r2
                d_beta = abs(c2 * beta[j] - wolves[i][j])
                x2 = beta[j] - a2 * d_beta

                r1, r2 = random.random(), random.random()
                a3 = 2 * a * r1 - a
                c3 = 2 * r2
                d_delta = abs(c3 * delta[j] - wolves[i][j])
                x3 = delta[j] - a3 * d_delta

                wolves[i][j] = (x1 + x2 + x3) / 3.0
    return best_params, alpha_s


def firefly_optimize(objective: ObjectiveFn, dims: List[SearchDimension], population: int = 8, iterations: int = 4):
    fireflies = [_random_vector(dims) for _ in range(population)]
    alpha = 0.2
    beta0 = 1.0
    gamma = 1.0
    best_score = -1e18
    best_params: Dict[str, float] = {}

    for _ in range(iterations):
        scores = []
        for f in fireflies:
            s, p = _score_candidate(f, dims, objective)
            scores.append((s, p))
            if s > best_score:
                best_score = s
                best_params = p
        for i in range(population):
            for j in range(population):
                if scores[j][0] > scores[i][0]:
                    r2 = sum((fireflies[i][k] - fireflies[j][k]) ** 2 for k in range(len(dims)))
                    beta = beta0 * math.exp(-gamma * r2)
                    for k in range(len(dims)):
                        step = beta * (fireflies[j][k] - fireflies[i][k])
                        noise = alpha * (random.random() - 0.5)
                        fireflies[i][k] += step + noise
    return best_params, best_score


def woa_optimize(objective: ObjectiveFn, dims: List[SearchDimension], population: int = 8, iterations: int = 4):
    whales = [_random_vector(dims) for _ in range(population)]
    best = whales[0][:]
    best_score = -1e18
    best_params: Dict[str, float] = {}

    for t in range(iterations):
        for w in whales:
            s, p = _score_candidate(w, dims, objective)
            if s > best_score:
                best_score = s
                best = w[:]
                best_params = p

        a = 2 - 2 * t / max(1, iterations - 1)
        for i in range(population):
            p = random.random()
            for j in range(len(dims)):
                if p < 0.5:
                    r1, r2 = random.random(), random.random()
                    A = 2 * a * r1 - a
                    C = 2 * r2
                    if abs(A) < 1:
                        D = abs(C * best[j] - whales[i][j])
                        whales[i][j] = best[j] - A * D
                    else:
                        rand_w = whales[random.randint(0, population - 1)]
                        D = abs(C * rand_w[j] - whales[i][j])
                        whales[i][j] = rand_w[j] - A * D
                else:
                    l = random.uniform(-1.0, 1.0)
                    D = abs(best[j] - whales[i][j])
                    whales[i][j] = D * math.exp(1.0 * l) * math.cos(2 * math.pi * l) + best[j]
    return best_params, best_score


def abc_optimize(objective: ObjectiveFn, dims: List[SearchDimension], population: int = 8, iterations: int = 4):
    foods = [_random_vector(dims) for _ in range(population)]
    scores = []
    params_cache = []
    for f in foods:
        s, p = _score_candidate(f, dims, objective)
        scores.append(s)
        params_cache.append(p)
    trial = [0] * population
    limit = max(3, population // 2)

    best_idx = max(range(population), key=lambda i: scores[i])
    best_score = scores[best_idx]
    best_params = params_cache[best_idx]

    for _ in range(iterations):
        # employed bees
        for i in range(population):
            k = random.choice([x for x in range(population) if x != i])
            j = random.randrange(len(dims))
            phi = random.uniform(-1.0, 1.0)
            cand = foods[i][:]
            cand[j] = foods[i][j] + phi * (foods[i][j] - foods[k][j])
            s, p = _score_candidate(cand, dims, objective)
            if s > scores[i]:
                foods[i], scores[i], params_cache[i], trial[i] = cand, s, p, 0
            else:
                trial[i] += 1

        # onlooker bees
        min_s = min(scores)
        probs = [(s - min_s + 1e-6) for s in scores]
        sm = sum(probs)
        probs = [p / sm for p in probs]
        for _ in range(population):
            i = random.choices(range(population), weights=probs, k=1)[0]
            k = random.choice([x for x in range(population) if x != i])
            j = random.randrange(len(dims))
            phi = random.uniform(-1.0, 1.0)
            cand = foods[i][:]
            cand[j] = foods[i][j] + phi * (foods[i][j] - foods[k][j])
            s, p = _score_candidate(cand, dims, objective)
            if s > scores[i]:
                foods[i], scores[i], params_cache[i], trial[i] = cand, s, p, 0
            else:
                trial[i] += 1

        # scout bees
        for i in range(population):
            if trial[i] > limit:
                foods[i] = _random_vector(dims)
                scores[i], params_cache[i] = _score_candidate(foods[i], dims, objective)
                trial[i] = 0

        best_idx = max(range(population), key=lambda idx: scores[idx])
        if scores[best_idx] > best_score:
            best_score = scores[best_idx]
            best_params = params_cache[best_idx]

    return best_params, best_score


def sa_optimize(objective: ObjectiveFn, dims: List[SearchDimension], iterations: int = 24):
    current = _random_vector(dims)
    current_score, current_params = _score_candidate(current, dims, objective)
    best, best_score, best_params = current[:], current_score, current_params
    t = 1.0
    cooling = 0.90

    for _ in range(iterations):
        cand = current[:]
        idx = random.randrange(len(dims))
        step = (dims[idx].high - dims[idx].low) * 0.15
        cand[idx] += random.uniform(-step, step)
        cand_score, cand_params = _score_candidate(cand, dims, objective)
        delta = cand_score - current_score
        if delta > 0 or random.random() < math.exp(delta / max(1e-6, t)):
            current, current_score, current_params = cand, cand_score, cand_params
        if current_score > best_score:
            best, best_score, best_params = current[:], current_score, current_params
        t *= cooling

    return best_params, best_score

